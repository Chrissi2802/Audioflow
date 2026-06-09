"""Tests for download engine"""

from pathlib import Path
from unittest.mock import patch, Mock

import pytest

from audioflow.core.downloader import AudioDownloader
from audioflow.models.download import (
    DownloadRequest,
    DownloadResult,
    DownloadStatus,
    BatchDownloadRequest,
    AudioQuality,
)


class TestAudioDownloader:
    """Tests for AudioDownloader class"""

    def test_create_ytdlp_options(self, downloader, sample_download_request, temp_output_dir):
        """Test yt-dlp options creation"""
        sample_download_request.output_path = temp_output_dir
        
        options = downloader._create_ytdlp_options(sample_download_request)
        
        assert options["audioquality"] == "192"
        assert str(temp_output_dir) in options["outtmpl"]
        assert "progress_hooks" in options
        assert len(options["postprocessors"]) == 1
        assert options["postprocessors"][0]["key"] == "FFmpegExtractAudio"

    def test_create_ytdlp_options_custom_filename(self, downloader, sample_download_request, temp_output_dir):
        """Test yt-dlp options with custom filename"""
        sample_download_request.output_path = temp_output_dir
        sample_download_request.custom_filename = "custom_name"
        
        options = downloader._create_ytdlp_options(sample_download_request)
        
        assert "custom_name" in options["outtmpl"]

    def test_create_ytdlp_options_organize_by_artist(self, downloader, sample_download_request, temp_output_dir):
        """Test yt-dlp options with artist organization"""
        from audioflow.core.config import config
        
        original_organize = config.organize_by_artist
        config.organize_by_artist = True
        
        try:
            sample_download_request.output_path = temp_output_dir
            options = downloader._create_ytdlp_options(sample_download_request)
            
            assert "%(uploader)s" in options["outtmpl"]
        finally:
            config.organize_by_artist = original_organize

    @pytest.mark.asyncio
    async def test_download_single_success(self, downloader, sample_download_request, mock_ytdlp, temp_output_dir):
        """Test successful single download"""
        sample_download_request.output_path = temp_output_dir
        
        # Mock the file path resolution
        with patch.object(downloader, '_get_downloaded_file_path') as mock_path:
            mock_file = temp_output_dir / "test.mp3"
            mock_file.touch()  # Create the file
            mock_path.return_value = mock_file
            
            # Mock embed_metadata
            with patch('audioflow.core.downloader.embed_metadata') as mock_embed:
                mock_embed.return_value = True
                
                result = await downloader.download_single(sample_download_request)
        
        assert result.status == DownloadStatus.COMPLETED
        assert result.title == "Test Song"
        assert result.artist == "Test Artist"
        assert result.album == "Test Album"
        assert result.file_path == mock_file
        assert result.download_time is not None

    @pytest.mark.asyncio
    async def test_download_single_failure(self, downloader, sample_download_request, mock_ytdlp_failed):
        """Test failed single download"""
        result = await downloader.download_single(sample_download_request)
        
        assert result.status == DownloadStatus.FAILED
        assert "Network error" in result.error_message
        assert result.download_time is not None

    @pytest.mark.asyncio
    async def test_batch_download(self, downloader, temp_output_dir):
        """Test batch download"""
        requests = [
            DownloadRequest(url=f"https://youtube.com/watch?v=test{i}", quality=AudioQuality.LOW)
            for i in range(3)
        ]
        
        batch_request = BatchDownloadRequest(requests=requests, concurrent_limit=2)
        
        # Mock all downloads as successful
        with patch.object(downloader, 'download_single') as mock_download:
            mock_download.return_value = DownloadResult(
                request=requests[0],
                status=DownloadStatus.COMPLETED,
                title="Test",
                artist="Artist",
                download_time=1.0
            )
            
            result = await downloader.download_batch(batch_request)
        
        assert result.total_requests == 3
        assert len(result.successful) == 3
        assert len(result.failed) == 0
        assert result.success_rate == 1.0
        assert result.total_time > 0

    @pytest.mark.asyncio
    async def test_batch_download_mixed_results(self, downloader):
        """Test batch download with mixed success/failure"""
        requests = [
            DownloadRequest(url=f"https://youtube.com/watch?v=test{i}", quality=AudioQuality.LOW)
            for i in range(4)
        ]
        
        batch_request = BatchDownloadRequest(requests=requests, concurrent_limit=2)
        
        # Mock alternating success/failure
        def mock_download_side_effect(request):
            if "test0" in str(request.url) or "test2" in str(request.url):
                return DownloadResult(
                    request=request,
                    status=DownloadStatus.COMPLETED,
                    title="Success",
                    artist="Artist"
                )
            else:
                return DownloadResult(
                    request=request,
                    status=DownloadStatus.FAILED,
                    error_message="Test failure"
                )
        
        with patch.object(downloader, 'download_single', side_effect=mock_download_side_effect):
            result = await downloader.download_batch(batch_request)
        
        assert result.total_requests == 4
        assert len(result.successful) == 2
        assert len(result.failed) == 2
        assert result.success_rate == 0.5

    @pytest.mark.asyncio
    async def test_retry_failed_downloads(self, downloader):
        """Test retry mechanism for failed downloads"""
        failed_request = DownloadRequest(url="https://youtube.com/watch?v=failed")
        failed_result = DownloadResult(
            request=failed_request,
            status=DownloadStatus.FAILED,
            error_message="Initial failure"
        )
        
        # Mock successful retry
        with patch.object(downloader, 'download_batch') as mock_batch:
            successful_result = DownloadResult(
                request=failed_request,
                status=DownloadStatus.COMPLETED,
                title="Retry Success"
            )
            
            from audioflow.models.download import BatchDownloadResult
            mock_batch.return_value = BatchDownloadResult(
                total_requests=1,
                successful=[successful_result],
                failed=[],
                total_time=1.0,
                success_rate=1.0
            )
            
            retry_result = await downloader.retry_failed_downloads([failed_result], max_retries=2)
        
        assert len(retry_result.successful) == 1
        assert len(retry_result.failed) == 0
        assert retry_result.success_rate == 1.0

    @pytest.mark.asyncio
    async def test_retry_failed_downloads_empty(self, downloader):
        """Test retry with empty failed list"""
        retry_result = await downloader.retry_failed_downloads([])
        
        assert retry_result.total_requests == 0
        assert len(retry_result.successful) == 0
        assert len(retry_result.failed) == 0
        assert retry_result.success_rate == 1.0

    def test_get_downloaded_file_path(self, downloader):
        """Test file path resolution"""
        template = "/output/%(uploader)s/%(title)s.%(ext)s"
        info = {
            "title": "Test Song",
            "uploader": "Test Artist",
        }
        
        result_path = downloader._get_downloaded_file_path(template, info)
        
        assert result_path is not None
        assert "Test Song" in str(result_path)
        assert "Test Artist" in str(result_path)
        assert str(result_path).endswith(".mp3")

    def test_get_downloaded_file_path_error(self, downloader):
        """Test file path resolution with error"""
        template = "/output/%(invalid_key)s.%(ext)s"
        info = {"title": "Test"}
        
        # This should handle the error gracefully
        result_path = downloader._get_downloaded_file_path(template, info)
        
        # The implementation should return None on error
        assert result_path is None or isinstance(result_path, Path)


class TestDownloaderConfiguration:
    """Tests for downloader configuration"""

    def test_downloader_max_workers(self):
        """Test downloader with custom max workers"""
        downloader = AudioDownloader(max_workers=5)
        assert downloader.max_workers == 5

    def test_downloader_default_max_workers(self):
        """Test downloader with default max workers"""
        downloader = AudioDownloader()
        # Should use config default
        from audioflow.core.config import config
        assert downloader.max_workers == config.max_concurrent_downloads

    def test_progress_hook(self, downloader):
        """Test progress hook functionality"""
        # Test downloading status
        download_data = {
            "status": "downloading",
            "_percent_str": "50%",
            "_speed_str": "1MB/s"
        }
        
        # Should not raise exception
        downloader._progress_hook(download_data)
        
        # Test finished status
        finished_data = {
            "status": "finished",
            "filename": "/path/to/file.mp3"
        }
        
        # Should not raise exception
        downloader._progress_hook(finished_data)