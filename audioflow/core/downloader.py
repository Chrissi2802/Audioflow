import logging
from pathlib import Path
from typing import Any, Dict, Optional

import yt_dlp
from tenacity import retry, stop_after_attempt, wait_fixed

from audioflow.models import AudioMetaData


logger = logging.getLogger(__name__)


class AudioDownloader:
    """Handles interactions with yt-dlp to extract metadata and download audio."""

    def __init__(self, temp_dir: Optional[Path] = None) -> None:
        """Initializes the AudioDownloader with an optional temporary directory.

        Args:
            temp_dir (Optional[Path], optional): The directory to store temporary files.
                Defaults to None.
        """

        self.temp_dir = temp_dir or Path("temp_downloads")
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def validate_url(self, url: str) -> bool:
        """Checks if the provided URL is supported by yt-dlp extractors.

        Args:
            url (str): The URL to validate.

        Returns:
            bool: True if the URL is supported, False otherwise.
        """

        extractors = yt_dlp.extractor.gen_extractors()
        for extractor in extractors:
            if extractor.suitable(url) and extractor.IE_NAME != "generic":
                return True
        return False

    def extract_info(self, url: str) -> AudioMetaData:
        """Fetches metadata without downloading the file.

        Args:
            url (str): The URL to extract metadata from.

        Returns:
            AudioMetaData: The extracted metadata.
        """

        ydl_opts = {
            "quiet": True,
            "skip_download": True,
            "extract_flat": "in_playlist",  # Don't expand playlists fully
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                return self._parse_metadata(info, url)
            except Exception as e:
                logger.error(f"Failed to extract info for {url}: {e}")
                raise

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def download(
        self, url: str, audio_format: str = "mp3", quality: str = "192"
    ) -> Path:
        """Downloads the audio from the URL to a temporary file.
        Retries up to 3 times on failure.

        Args:
            url (str): The URL to download audio from.
            audio_format (str, optional): The format of the audio to download.
                Defaults to "mp3".
            quality (str, optional): The quality of the audio to download.
                Defaults to "192".

        Returns:
            Path: The path to the downloaded audio file.
        """

        filename_template = f"{self.temp_dir}/%(id)s.%(ext)s"

        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": filename_template,
            "quiet": True,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": audio_format,
                    "preferredquality": quality,
                }
            ],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=True)
                # yt-dlp might return a list for playlists,
                # but here we assume single video download logic
                # For batch processing, the calling service should iterate.
                if "entries" in info:
                    # Fallback if a playlist URL was passed
                    # to this single-download method
                    info = info["entries"][0]

                # Determine the final output path
                # Note: FFmpeg postprocessor changes the extension
                file_id = info["id"]
                final_path = self.temp_dir / f"{file_id}.{audio_format}"

                if not final_path.exists():
                    # Fallback check, sometimes filename is different
                    extracted_filename = ydl.prepare_filename(info)
                    final_path = Path(extracted_filename).with_suffix(
                        f".{audio_format}"
                    )

                return final_path

            except Exception as e:
                logger.error(f"Download failed for {url}: {e}")
                raise

    def _parse_metadata(self, info: Dict[str, Any], url: str) -> AudioMetaData:
        """Converts yt-dlp info dict to AudioMetaData model.

        Args:
            info (Dict[str, Any]): The yt-dlp info dict.
            url (str): The URL of the audio.

        Returns:
            AudioMetaData: The AudioMetaData model.
        """

        return AudioMetaData(
            title=info.get("title", "Unknown Title"),
            artist=info.get("artist"),
            album=info.get("album"),
            duration=info.get("duration"),
            url=url,
            thumbnail_url=info.get("thumbnail"),
            source_id=info.get("id"),
        )


if __name__ == "__main__":
    pass
