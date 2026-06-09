"""AudioFlow - Modern audio download tool"""

__version__ = "0.1.0"
__author__ = "Christopher"
__license__ = "Apache-2.0"

from .cli import cli
from .core.downloader import AudioDownloader
from .models.download import DownloadRequest, DownloadResult

__all__ = ["cli", "AudioDownloader", "DownloadRequest", "DownloadResult"]