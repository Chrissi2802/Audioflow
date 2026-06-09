"""Data models for download operations"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl, validator


class DownloadStatus(str, Enum):
    """Status of a download operation"""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AudioQuality(str, Enum):
    """Audio quality options"""
    LOW = "128"
    MEDIUM = "192"
    HIGH = "256"
    ULTRA = "320"


class DownloadRequest(BaseModel):
    """Single download request"""
    url: HttpUrl
    quality: AudioQuality = AudioQuality.MEDIUM
    output_path: Optional[Path] = None
    custom_filename: Optional[str] = None

    @validator("url")
    def validate_url(cls, v: HttpUrl) -> HttpUrl:
        """Validate URL is from supported platform"""
        url_str = str(v)
        supported_platforms = [
            "youtube.com",
            "youtu.be",
            "soundcloud.com",
            "bandcamp.com",
        ]
        
        if not any(platform in url_str for platform in supported_platforms):
            raise ValueError(f"Unsupported platform. Supported: {supported_platforms}")
        return v


class DownloadResult(BaseModel):
    """Result of a download operation"""
    request: DownloadRequest
    status: DownloadStatus
    file_path: Optional[Path] = None
    file_size: Optional[int] = None
    duration: Optional[float] = None
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    error_message: Optional[str] = None
    download_time: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.now)


class BatchDownloadRequest(BaseModel):
    """Batch download for multiple URLs"""
    requests: List[DownloadRequest]
    concurrent_limit: int = Field(default=3, ge=1, le=10)

    @validator("requests")
    def validate_requests_not_empty(cls, v: List[DownloadRequest]) -> List[DownloadRequest]:
        """Ensure requests list is not empty"""
        if not v:
            raise ValueError("Requests list cannot be empty")
        return v


class BatchDownloadResult(BaseModel):
    """Result of a batch download operation"""
    total_requests: int
    successful: List[DownloadResult]
    failed: List[DownloadResult]
    total_time: float
    success_rate: float

    @validator("success_rate", pre=True, always=True)
    def calculate_success_rate(cls, v: Optional[float], values: dict) -> float:
        """Calculate success rate from successful and total requests"""
        if v is not None:
            return v
        
        total = values.get("total_requests", 0)
        successful = len(values.get("successful", []))
        
        return successful / total if total > 0 else 0.0