"""CLI interface for AudioFlow"""

import asyncio
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.text import Text

from .core.config import config
from .core.downloader import AudioDownloader
from .core.utils import format_duration, format_file_size, parse_urls_from_file, setup_logging
from .models.download import AudioQuality, BatchDownloadRequest, DownloadRequest

console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="audioflow")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option("--config-file", type=click.Path(exists=True), help="Configuration file path")
@click.pass_context
def cli(ctx: click.Context, verbose: bool, config_file: Optional[str]) -> None:
    """AudioFlow - Modern audio download tool"""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose

    setup_logging(verbose)

    if config_file:
        # TODO: Implement config file loading
        console.print(f"[yellow]Config file support coming soon: {config_file}[/yellow]")


@cli.command()
@click.argument("url")
@click.option(
    "--quality",
    "-q",
    type=click.Choice(["128", "192", "256", "320"]),
    default="192",
    help="Audio quality in kbps",
)
@click.option("--output", "-o", type=click.Path(), help="Output directory")
@click.option("--filename", "-n", help="Custom filename (without extension)")
@click.pass_context
def download(
    ctx: click.Context, url: str, quality: str, output: Optional[str], filename: Optional[str]
) -> None:
    """Download single audio from URL"""

    try:
        # Create download request
        request = DownloadRequest(
            url=url,
            quality=AudioQuality(quality),
            output_path=Path(output) if output else None,
            custom_filename=filename,
        )

        console.print(
            Panel(
                f"🎵 Starting download from: [blue]{url}[/blue]",
                title="AudioFlow Download",
                border_style="blue",
            )
        )

        # Initialize downloader
        downloader = AudioDownloader()

        # Download with progress
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Downloading...", total=100)
            
            # Run async download
            result = asyncio.run(downloader.download_single(request))
            progress.update(task, completed=100)

        # Display result
        if result.status.value == "completed":
            _display_success_result(result)
        else:
            _display_error_result(result)
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        if ctx.obj["verbose"]:
            console.print_exception()
        sys.exit(1)


@cli.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.option(
    "--quality",
    "-q",
    type=click.Choice(["128", "192", "256", "320"]),
    default="192",
    help="Audio quality in kbps",
)
@click.option("--output", "-o", type=click.Path(), help="Output directory")
@click.option("--concurrent", "-c", default=3, help="Number of concurrent downloads")
@click.option("--retry", is_flag=True, help="Retry failed downloads")
@click.pass_context
def batch(
    ctx: click.Context,
    file_path: str,
    quality: str,
    output: Optional[str],
    concurrent: int,
    retry: bool,
) -> None:
    """Download multiple audios from URL list file"""

    try:
        # Parse URLs from file
        urls = parse_urls_from_file(Path(file_path))

        if not urls:
            console.print("[red]Error:[/red] No valid URLs found in file")
            sys.exit(1)

        console.print(f"📄 Found {len(urls)} valid URLs in file")

        # Create batch request
        requests = [
            DownloadRequest(
                url=url, quality=AudioQuality(quality), output_path=Path(output) if output else None
            )
            for url in urls
        ]

        batch_request = BatchDownloadRequest(requests=requests, concurrent_limit=concurrent)

        console.print(
            Panel(
                f"🚀 Starting batch download of [bold]{len(urls)}[/bold] items",
                title="AudioFlow Batch Download",
                border_style="green",
            )
        )

        # Initialize downloader
        downloader = AudioDownloader()

        # Batch download with progress
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Processing batch...", total=len(urls))

            result = asyncio.run(downloader.download_batch(batch_request))
            progress.update(task, completed=len(urls))

        # Display results
        _display_batch_results(result)

        # Retry failed downloads if requested
        if retry and result.failed:
            console.print("\n[yellow]Retrying failed downloads...[/yellow]")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console,
            ) as progress:
                task = progress.add_task("Retrying failures...", total=len(result.failed))
                
                retry_result = asyncio.run(downloader.retry_failed_downloads(result.failed))
                progress.update(task, completed=len(result.failed))

            console.print(f"\n[green]Retry completed:[/green]")
            console.print(f"  • Additional successes: {len(retry_result.successful)}")
            console.print(f"  • Still failed: {len(retry_result.failed)}")

        if result.failed and not retry:
            console.print(f"\n[yellow]Tip:[/yellow] Use --retry flag to automatically retry failed downloads")
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        if ctx.obj["verbose"]:
            console.print_exception()
        sys.exit(1)


@cli.command("config")
def config_show() -> None:
    """Show current configuration"""

    table = Table(title="AudioFlow Configuration", border_style="cyan")
    table.add_column("Setting", style="cyan", no_wrap=True)
    table.add_column("Value", style="green")

    table.add_row("Output Directory", str(config.output_dir))
    table.add_row("Audio Quality", config.audio_quality + " kbps")
    table.add_row("Audio Format", config.audio_format.upper())
    table.add_row("Max Concurrent", str(config.max_concurrent_downloads))
    table.add_row("Max Retries", str(config.max_retries))
    table.add_row("Organize by Artist", "✓" if config.organize_by_artist else "✗")
    table.add_row("Create Date Folders", "✓" if config.create_date_folders else "✗")

    console.print(table)


@cli.command()
@click.argument("url")
def info(url: str) -> None:
    """Get information about a URL without downloading"""
    try:
        import yt_dlp

        console.print(f"🔍 Extracting information from: [blue]{url}[/blue]")

        with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
            info = ydl.extract_info(url, download=False)

        if info:
            table = Table(title="Media Information", border_style="blue")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="white")

            table.add_row("Title", info.get("title", "Unknown"))
            table.add_row("Uploader", info.get("uploader", "Unknown"))
            table.add_row("Duration", format_duration(info.get("duration")))
            table.add_row("View Count", f"{info.get('view_count', 0):,}" if info.get('view_count') else "Unknown")
            table.add_row("Upload Date", info.get("upload_date", "Unknown"))
            table.add_row("Description", (info.get("description", "")[:100] + "...") if info.get("description") else "No description")

            console.print(table)
        else:
            console.print("[red]Could not extract information from URL[/red]")

    except Exception as e:
        console.print(f"[red]Error extracting info:[/red] {str(e)}")
        sys.exit(1)


def _display_success_result(result) -> None:
    """Display successful download result"""
    table = Table(title="✅ Download Completed", border_style="green")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Title", result.title or "Unknown")
    table.add_row("Artist", result.artist or "Unknown")
    table.add_row("Album", result.album or "Not specified")
    table.add_row("File Path", str(result.file_path) if result.file_path else "Unknown")
    table.add_row("File Size", format_file_size(result.file_size))
    table.add_row("Duration", format_duration(result.duration))
    table.add_row("Quality", f"{result.request.quality.value} kbps")
    table.add_row("Download Time", f"{result.download_time:.1f}s" if result.download_time else "Unknown")

    console.print(table)


def _display_error_result(result) -> None:
    """Display failed download result"""
    console.print(Panel(
        f"[red]❌ Download Failed[/red]\n\n[red]Error:[/red] {result.error_message}",
        border_style="red",
        title="Download Error"
    ))


def _display_batch_results(result) -> None:
    """Display batch download results"""
    # Summary
    summary_table = Table(title="📊 Batch Download Results", border_style="blue")
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", style="white")

    summary_table.add_row("Total Requests", str(result.total_requests))
    summary_table.add_row("Successful", f"[green]{len(result.successful)}[/green]")
    summary_table.add_row("Failed", f"[red]{len(result.failed)}[/red]")
    summary_table.add_row("Success Rate", f"{result.success_rate:.1%}")
    summary_table.add_row("Total Time", f"{result.total_time:.1f}s")

    console.print(summary_table)

    # Successful downloads
    if result.successful:
        console.print("\n[green]✅ Successful Downloads:[/green]")
        success_table = Table(border_style="green")
        success_table.add_column("Title", style="green")
        success_table.add_column("Artist", style="cyan")
        success_table.add_column("Size", style="yellow")

        for success in result.successful[:10]:  # Show first 10
            success_table.add_row(
                success.title or "Unknown",
                success.artist or "Unknown",
                format_file_size(success.file_size)
            )

        console.print(success_table)
        
        if len(result.successful) > 10:
            console.print(f"[dim]... and {len(result.successful) - 10} more successful downloads[/dim]")

    # Failed downloads
    if result.failed:
        console.print(f"\n[red]❌ Failed Downloads ({len(result.failed)}):[/red]")
        
        if console.confirm("Show detailed error information?"):
            fail_table = Table(border_style="red")
            fail_table.add_column("URL", style="cyan", max_width=50)
            fail_table.add_column("Error", style="red", max_width=50)

            for failed in result.failed[:5]:  # Show first 5 failures
                fail_table.add_row(
                    str(failed.request.url)[:47] + "..." if len(str(failed.request.url)) > 50 else str(failed.request.url),
                    failed.error_message or "Unknown error"
                )

            console.print(fail_table)
            
            if len(result.failed) > 5:
                console.print(f"[dim]... and {len(result.failed) - 5} more failed downloads[/dim]")


if __name__ == "__main__":
    cli()