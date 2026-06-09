import re
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class AudioMetaData(BaseModel):
    """Represents metadata extracted from an audio source (e.g. YouTube video)."""

    title: str = Field(..., description="The title of the track")

    @field_validator("title")
    @classmethod
    def clean_title(cls, v: str) -> str:
        """Removes common clutter patterns from the title."""

        patterns = [
            r"\(Official Video\)",
            r"\(Official Audio\)",
            r"\(Lyric Video\)",
            r"\(Official Lyric Video\)",
            r"\[Official Video\]",
            r"\(4K\)",
            r"\(HD\)",
        ]

        cleaned = v
        for pattern in patterns:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

        # Cleans up double spaces and whitespace at the margins
        return re.sub(r"\s+", " ", cleaned).strip()

    artist: Optional[str] = Field(None, description="The artist name")
    album: Optional[str] = Field(None, description="The album name")
    duration: Optional[float] = Field(None, description="Duration in seconds")
    url: str = Field(..., description="Original URL of the source")
    thumbnail_url: Optional[str] = Field(None, description="URL to the thumbnail image")
    source_id: Optional[str] = Field(
        None, description="Unique ID from the source platform"
    )

    class Config:
        frozen = True  # Make it immutable (hashable) if needed


if __name__ == "__main__":
    pass
