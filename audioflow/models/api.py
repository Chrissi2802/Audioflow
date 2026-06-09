from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl


class DownloadRequest(BaseModel):
    """Input model for initiating a download."""

    urls: List[HttpUrl] = Field(
        ..., description="List of URLs to download", min_items=1
    )
    extract_audio: bool = Field(
        default=True, description="Whether to extract audio (True) or keep video"
    )
    audio_format: str = Field(
        default="mp3", description="Target audio format (mp3, m4a, etc.)"
    )
    quality: str = Field(default="192", description="Target audio bitrate")

    # Optional grouping or tagging for this batch
    batch_name: Optional[str] = Field(
        None, description="Optional name for this download batch"
    )


if __name__ == "__main__":
    pass
