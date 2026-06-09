"""Tests for data models"""

import pytest
from pydantic import ValidationError

from audioflow.models.download import (
    DownloadRequest,
    AudioQuality,
    DownloadResult,
    DownloadStatus,
    BatchDownloadRequest,
    BatchDownloadResult,
)


class TestDownloadRequest:
    """Tests for DownloadRequest model"""

    def test_valid_request(self):
        """Test creating valid download request"""
        request = DownloadRequest(
            url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            quality=AudioQuality.HIGH
        )
        
        assert str(request.url) == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        assert request.quality == AudioQuality.HIGH
        assert request.output_path is None
        assert request.custom_filename is None

    def test_unsupported_platform(self):
        """Test validation with unsupported platform"""
        with pytest.raises(ValidationError) as exc_info:
            DownloadRequest(url="https://unsupported.com/video")
        
        assert "Unsupported platform" in str(exc_info.value)

    def test_supported_platforms(self):
        """Test all supported platforms"""
        supported_urls = [
            "https://www.youtube.com/watch?v=test",
            "https://youtu.be/test",
            "https://soundcloud.com/artist/track",
            "https://artist.bandcamp.com/track/song",
        ]
        
        for url in supported_urls:
            request = DownloadRequest(url=url)
            assert str(request.url) == url

    def test_audio_quality_enum(self):
        """Test audio quality enum values"""
        assert AudioQuality.LOW.value == "128"
        assert AudioQuality.MEDIUM.value == "192"
        assert AudioQuality.HIGH.value == "256"
        assert AudioQuality.ULTRA.value == "320"


class TestBatchDownloadRequest:
    """Tests for BatchDownloadRequest model"""

    def test_valid_batch_request(self, sample_urls):
        """Test creating valid batch request"""
        requests = [DownloadRequest(url=url) for url in sample_urls]
        batch_request = BatchDownloadRequest(requests=requests, concurrent_limit=2)
        
        assert len(batch_request.requests) == len(sample_urls)
        assert batch_request.concurrent_limit == 2

    def test_empty_requests_validation(self):
        """Test validation with empty requests list"""
        with pytest.raises(ValidationError) as exc_info:
            BatchDownloadRequest(requests=[])
        
        assert "Requests list cannot be empty" in str(exc_info.value)

    def test_concurrent_limit_validation(self):
        """Test concurrent limit boundaries"""
        request = DownloadRequest(url="https://youtube.com/watch?v=test")
        
        # Valid limits
        BatchDownloadRequest(requests=[request], concurrent_limit=1)
        BatchDownloadRequest(requests=[request], concurrent_limit=10)
        
        # Invalid limits should use Field validation
        with pytest.raises(ValidationError):
            BatchDownloadRequest(requests=[request], concurrent_limit=0)
        
        with pytest.raises(ValidationError):
            BatchDownloadRequest(requests=[request], concurrent_limit=11)


class TestDownloadResult:
    """Tests for DownloadResult model"""

    def test_download_result_creation(self, sample_download_request):
        """Test creating download result"""
        result = DownloadResult(
            request=sample_download_request,
            status=DownloadStatus.COMPLETED,
            title="Test Song",
            artist="Test Artist"
        )
        
        assert result.request == sample_download_request
        assert result.status == DownloadStatus.COMPLETED
        assert result.title == "Test Song"
        assert result.artist == "Test Artist"
        assert result.created_at is not None


class TestBatchDownloadResult:
    """Tests for BatchDownloadResult model"""

    def test_success_rate_calculation(self, sample_download_request):
        """Test automatic success rate calculation"""
        successful = [
            DownloadResult(
                request=sample_download_request,
                status=DownloadStatus.COMPLETED
            )
        ]
        failed = [
            DownloadResult(
                request=sample_download_request,
                status=DownloadStatus.FAILED,
                error_message="Test error"
            )
        ]
        
        result = BatchDownloadResult(
            total_requests=2,
            successful=successful,
            failed=failed,
            total_time=10.0
        )
        
        assert result.success_rate == 0.5
        assert result.total_requests == 2
        assert len(result.successful) == 1
        assert len(result.failed) == 1

    def test_empty_batch_result(self):
        """Test batch result with no requests"""
        result = BatchDownloadResult(
            total_requests=0,
            successful=[],
            failed=[],
            total_time=0.0
        )
        
        assert result.success_rate == 0.0