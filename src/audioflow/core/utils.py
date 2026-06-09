"""Utility functions for AudioFlow"""

import logging
import re
import unicodedata
from pathlib import Path
from typing import List, Optional


def sanitize_filename(filename: str) -> str:
    """Clean filename from invalid characters"""
    # Normalize unicode
    filename = unicodedata.normalize("NFKD", filename)

    # Remove/replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', "_", filename)
    filename = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", filename)

    # Reduce multiple underscores
    filename = re.sub(r"_{2,}", "_", filename)

    # Remove leading/trailing dots and spaces
    filename = filename.strip(". ")

    # Limit length for Windows compatibility
    if len(filename) > 200:
        filename = filename[:200].rsplit(" ", 1)[0]

    return filename or "untitled"


def format_duration(seconds: Optional[float]) -> str:
    """Format duration in readable format"""
    if seconds is None:
        return "Unknown"

    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"


def calculate_file_size(file_path: Path) -> Optional[int]:
    """Calculate file size in bytes"""
    try:
        return file_path.stat().st_size if file_path.exists() else None
    except OSError:
        return None


def format_file_size(size_bytes: Optional[int]) -> str:
    """Format file size in readable format"""
    if size_bytes is None:
        return "Unknown"

    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def validate_url(url: str) -> bool:
    """Basic URL validation"""
    url_pattern = re.compile(
        r"^https?://"  # http:// or https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+"
        r"[A-Z]{2,6}\.?|"  # domain...
        r"localhost|"  # localhost...
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or IP
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )
    return url_pattern.match(url) is not None


def parse_urls_from_file(file_path: Path) -> List[str]:
    """Read URLs from file"""
    urls = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line and not line.startswith("#"):
                    if validate_url(line):
                        urls.append(line)
                    else:
                        logging.warning(f"Invalid URL on line {line_num}: {line}")
    except Exception as e:
        logging.error(f"Error reading URLs from file {file_path}: {e}")

    return urls


def setup_logging(verbose: bool = False) -> None:
    """Configure logging"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def create_output_directory(path: Path, organize_by_artist: bool = False, artist: Optional[str] = None) -> Path:
    """Create output directory structure"""
    if organize_by_artist and artist:
        sanitized_artist = sanitize_filename(artist)
        output_path = path / sanitized_artist
    else:
        output_path = path

    output_path.mkdir(parents=True, exist_ok=True)
    return output_path


def embed_metadata(file_path: Path, title: Optional[str] = None, artist: Optional[str] = None, album: Optional[str] = None) -> bool:
    """Embed metadata in audio file using mutagen"""
    try:
        from mutagen.mp3 import MP3
        from mutagen.id3 import ID3, TIT2, TPE1, TALB

        if not file_path.exists() or file_path.suffix.lower() != ".mp3":
            return False

        audio = MP3(file_path, ID3=ID3)

        # Add ID3 tag if not present
        if audio.tags is None:
            audio.add_tags()

        # Set metadata
        if title:
            audio.tags["TIT2"] = TIT2(encoding=3, text=title)
        if artist:
            audio.tags["TPE1"] = TPE1(encoding=3, text=artist)
        if album:
            audio.tags["TALB"] = TALB(encoding=3, text=album)

        audio.save()
        return True

    except Exception as e:
        logging.error(f"Failed to embed metadata in {file_path}: {e}")
        return False