"""Core download engine with yt-dlp integration"""

import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, Optional

import yt_dlp

from ..models.download import (
    BatchDownloadRequest,
    BatchDownloadResult,
    DownloadRequest,
    DownloadResult,
    DownloadStatus,
)
from .config import config
from .utils import (
    calculate_file_size,
    create_output_directory,
    embed_metadata,
    sanitize_filename,
)

logger = logging.getLogger(__name__)


class AudioDownloader:
    """Central download engine with yt-dlp"""

    def __init__(self, max_workers: Optional[int] = None):
        self.max_workers = max_workers or config.max_concurrent_downloads
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)

    def _create_ytdlp_options(self, request: DownloadRequest) -> Dict[str, Any]:
        """Create yt-dlp options for specific request"""
        # Base options from config
        options = config.ytdlp_options.copy()

        # Set quality
        options["audioquality"] = request.quality.value
        options["format"] = f"bestaudio[abr<={request.quality.value}]/bestaudio/best"

        # Determine output path
        output_dir = request.output_path or config.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        # Custom filename template
        if request.custom_filename:
            options["outtmpl"] = str(output_dir / f"{request.custom_filename}.%(ext)s")
        else:
            if config.organize_by_artist:
                options["outtmpl"] = str(
                    output_dir / "%(uploader)s" / "%(title)s.%(ext)s"
                )
            else:
                options["outtmpl"] = str(output_dir / "%(title)s.%(ext)s")

        # Progress hook
        options["progress_hooks"] = [self._progress_hook]

        # Post-processor for MP3 conversion
        options["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": request.quality.value,
            }
        ]

        return options

    def _progress_hook(self, d: Dict[str, Any]) -> None:
        """Progress callback for yt-dlp"""
        if d["status"] == "downloading":
            percent = d.get("_percent_str", "N/A")
            speed = d.get("_speed_str", "N/A")
            logger.debug(f"Download progress: {percent} at {speed}")
        elif d["status"] == "finished":
            logger.info(f"Download completed: {d['filename']}")

    def _download_single_sync(self, request: DownloadRequest) -> DownloadResult:
        """Synchronous download of a single URL"""
        start_time = time.time()

        try:
            options = self._create_ytdlp_options(request)

            with yt_dlp.YoutubeDL(options) as ydl:
                # First extract metadata
                info = ydl.extract_info(str(request.url), download=False)

                if not info:
                    raise Exception("Could not extract video information")

                # Perform download
                ydl.download([str(request.url)])

                # Determine downloaded file path
                file_path = self._get_downloaded_file_path(options["outtmpl"], info)

                # Embed metadata if file exists
                if file_path and file_path.exists():
                    embed_metadata(
                        file_path,
                        title=info.get("title"),
                        artist=info.get("uploader"),
                        album=info.get("album"),
                    )

                return DownloadResult(
                    request=request,
                    status=DownloadStatus.COMPLETED,
                    file_path=file_path,
                    file_size=calculate_file_size(file_path) if file_path and file_path.exists() else None,
                    duration=info.get("duration"),
                    title=info.get("title"),
                    artist=info.get("uploader"),
                    album=info.get("album"),
                    download_time=time.time() - start_time,
                )

        except Exception as e:
            logger.error(f"Download failed for {request.url}: {str(e)}")
            return DownloadResult(
                request=request,
                status=DownloadStatus.FAILED,
                error_message=str(e),
                download_time=time.time() - start_time,
            )

    def _get_downloaded_file_path(self, template: str, info: Dict[str, Any]) -> Optional[Path]:
        """Determine final file path"""
        try:
            # Replace template variables
            filename = template
            filename = filename.replace("%(title)s", sanitize_filename(info.get("title", "unknown")))
            filename = filename.replace("%(uploader)s", sanitize_filename(info.get("uploader", "unknown")))
            filename = filename.replace("%(ext)s", "mp3")

            return Path(filename)
        except Exception as e:
            logger.error(f"Error determining file path: {e}")
            return None

    async def download_single(self, request: DownloadRequest) -> DownloadResult:
        """Async download of a single URL"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, self._download_single_sync, request
        )

    async def download_batch(self, batch_request: BatchDownloadRequest) -> BatchDownloadResult:
        """Async batch download of multiple URLs"""
        start_time = time.time()

        # Semaphore for concurrent limit
        semaphore = asyncio.Semaphore(batch_request.concurrent_limit)

        async def download_with_semaphore(request: DownloadRequest) -> DownloadResult:
            async with semaphore:
                return await self.download_single(request)

        # Start all downloads in parallel
        tasks = [download_with_semaphore(req) for req in batch_request.requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Categorize results
        successful = []
        failed = []

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Exception in asyncio.gather
                failed.append(
                    DownloadResult(
                        request=batch_request.requests[i],
                        status=DownloadStatus.FAILED,
                        error_message=str(result),
                    )
                )
            elif result.status == DownloadStatus.COMPLETED:
                successful.append(result)
            else:
                failed.append(result)

        total_time = time.time() - start_time
        success_rate = len(successful) / len(batch_request.requests) if batch_request.requests else 0

        return BatchDownloadResult(
            total_requests=len(batch_request.requests),
            successful=successful,
            failed=failed,
            total_time=total_time,
            success_rate=success_rate,
        )

    async def retry_failed_downloads(self, failed_results: list[DownloadResult], max_retries: int = 3) -> BatchDownloadResult:
        """Retry failed downloads with exponential backoff"""
        if not failed_results:
            return BatchDownloadResult(
                total_requests=0,
                successful=[],
                failed=[],
                total_time=0.0,
                success_rate=1.0,
            )

        start_time = time.time()
        retry_requests = [result.request for result in failed_results]
        
        successful = []
        still_failed = []

        for attempt in range(max_retries):
            if not retry_requests:
                break

            logger.info(f"Retry attempt {attempt + 1}/{max_retries} for {len(retry_requests)} failed downloads")

            # Wait with exponential backoff
            if attempt > 0:
                wait_time = config.retry_delay * (2 ** (attempt - 1))
                await asyncio.sleep(wait_time)

            # Retry downloads
            batch_request = BatchDownloadRequest(
                requests=retry_requests,
                concurrent_limit=min(2, config.max_concurrent_downloads)  # Be more conservative on retries
            )
            
            result = await self.download_batch(batch_request)
            
            # Update results
            successful.extend(result.successful)
            retry_requests = [r.request for r in result.failed]
            still_failed = result.failed

        total_time = time.time() - start_time
        total_requests = len(failed_results)
        success_rate = len(successful) / total_requests if total_requests > 0 else 0

        return BatchDownloadResult(
            total_requests=total_requests,
            successful=successful,
            failed=still_failed,
            total_time=total_time,
            success_rate=success_rate,
        )

    def __del__(self):
        """Cleanup"""
        if hasattr(self, "executor"):
            self.executor.shutdown(wait=True)