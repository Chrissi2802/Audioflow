"""Configuration management for AudioFlow"""

import os
from pathlib import Path
from typing import Dict, Any

from pydantic import BaseSettings, Field


class AudioFlowConfig(BaseSettings):
    """Central configuration for AudioFlow"""

    # Download settings
    output_dir: Path = Field(
        default_factory=lambda: Path.home() / "Downloads" / "AudioFlow"
    )
    audio_quality: str = Field(default="192", description="Audio quality: 128, 192, 256, 320")
    audio_format: str = Field(default="mp3", description="Output format")
    max_concurrent_downloads: int = Field(default=3, ge=1, le=10)

    # Retry settings
    max_retries: int = Field(default=3, ge=0, le=10)
    retry_delay: float = Field(default=1.0, ge=0.1)

    # File organization
    organize_by_artist: bool = Field(default=True)
    create_date_folders: bool = Field(default=False)

    # yt-dlp settings
    ytdlp_options: Dict[str, Any] = Field(
        default_factory=lambda: {
            "format": "bestaudio/best",
            "extractaudio": True,
            "audioformat": "mp3",
            "outtmpl": "%(artist)s - %(title)s.%(ext)s",
            "ignoreerrors": True,
            "no_warnings": True,
        }
    )

    class Config:
        env_prefix = "AUDIOFLOW_"
        case_sensitive = False


# Global config instance
config = AudioFlowConfig()