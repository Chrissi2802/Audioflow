"""Tests for CLI interface"""

from pathlib import Path
from unittest.mock import patch, Mock

import pytest
from click.testing import CliRunner

from audioflow.cli import cli
from audioflow.models.download import DownloadResult, DownloadStatus


class TestCLIBasic:
    """Tests for basic CLI functionality"""

    def test_cli_version(self):
        """Test version command"""
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])
        
        assert result.exit_code == 0
        assert "0.1.0" in result.output

    def test_cli_help(self):
        """Test help command"""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        
        assert result.exit_code == 0
        assert "AudioFlow" in result.output
        assert "download" in result.output
        assert "batch" in result.output
        assert "config" in result.output

    def test_verbose_option(self):
        """Test verbose option"""
        runner = CliRunner()
        result = runner.invoke(cli, ["--verbose", "--help"])
        
        assert result.exit_code == 0

    def test_config_file_option(self, temp_output_dir):
        """Test config file option"""
        config_file = temp_output_dir / "config.yaml"
        config_file.touch()
        
        runner = CliRunner()
        result = runner.invoke(cli, ["--config-file", str(config_file), "--help"])
        
        assert result.exit_code == 0


class TestDownloadCommand:
    """Tests for download command"""

    def test_download_help(self):
        """Test download command help"""
        runner = CliRunner()
        result = runner.invoke(cli, ["download", "--help"])
        
        assert result.exit_code == 0
        assert "Download single audio" in result.output

    @patch('audioflow.cli.AudioDownloader')
    @patch('audioflow.cli.asyncio.run')
    def test_download_command_success(self, mock_asyncio, mock_downloader_class):
        """Test successful download command"""
        # Mock successful download result
        mock_result = Mock()
        mock_result.status.value = "completed"
        mock_result.title = "Test Song"
        mock_result.artist = "Test Artist"
        mock_result.album = "Test Album"
        mock_result.file_path = Path("/test/file.mp3")
        mock_result.file_size = 5000000
        mock_result.duration = 180.0
        mock_result.download_time = 10.5
        mock_result.request.quality.value = "192"
        
        mock_downloader = Mock()
        mock_downloader.download_single.return_value = mock_result
        mock_downloader_class.return_value = mock_downloader
        mock_asyncio.return_value = mock_result
        
        runner = CliRunner()
        result = runner.invoke(cli, ["download", "https://youtube.com/watch?v=test"])
        
        assert result.exit_code == 0
        mock_asyncio.assert_called_once()

    @patch('audioflow.cli.AudioDownloader')
    @patch('audioflow.cli.asyncio.run')
    def test_download_command_failure(self, mock_asyncio, mock_downloader_class):
        """Test failed download command"""
        # Mock failed download result
        mock_result = Mock()
        mock_result.status.value = "failed"
        mock_result.error_message = "Download failed"
        
        mock_downloader = Mock()
        mock_downloader.download_single.return_value = mock_result
        mock_downloader_class.return_value = mock_downloader
        mock_asyncio.return_value = mock_result
        
        runner = CliRunner()
        result = runner.invoke(cli, ["download", "https://youtube.com/watch?v=test"])
        
        assert result.exit_code == 1

    def test_download_command_options(self):
        """Test download command with all options"""
        runner = CliRunner()
        
        # Test quality option
        result = runner.invoke(cli, ["download", "--help"])
        assert "--quality" in result.output
        assert "--output" in result.output
        assert "--filename" in result.output

    @patch('audioflow.cli.AudioDownloader')
    def test_download_invalid_url(self, mock_downloader_class):
        """Test download with invalid URL"""
        runner = CliRunner()
        result = runner.invoke(cli, ["download", "invalid-url"])
        
        # Should fail due to URL validation
        assert result.exit_code == 1


class TestBatchCommand:
    """Tests for batch command"""

    def test_batch_help(self):
        """Test batch command help"""
        runner = CliRunner()
        result = runner.invoke(cli, ["batch", "--help"])
        
        assert result.exit_code == 0
        assert "Download multiple audios" in result.output

    @patch('audioflow.cli.parse_urls_from_file')
    @patch('audioflow.cli.AudioDownloader')
    @patch('audioflow.cli.asyncio.run')
    def test_batch_command_success(self, mock_asyncio, mock_downloader_class, mock_parse_urls):
        """Test successful batch command"""
        # Mock URL parsing
        mock_parse_urls.return_value = [
            "https://youtube.com/watch?v=test1",
            "https://youtube.com/watch?v=test2"
        ]
        
        # Mock successful batch result
        from audioflow.models.download import BatchDownloadResult
        mock_batch_result = Mock()
        mock_batch_result.successful = []
        mock_batch_result.failed = []
        mock_batch_result.total_requests = 2
        mock_batch_result.success_rate = 1.0
        mock_batch_result.total_time = 20.0
        
        mock_downloader = Mock()
        mock_downloader_class.return_value = mock_downloader
        mock_asyncio.return_value = mock_batch_result
        
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create a test file
            with open("test_urls.txt", "w") as f:
                f.write("https://youtube.com/watch?v=test1\n")
                f.write("https://youtube.com/watch?v=test2\n")
            
            result = runner.invoke(cli, ["batch", "test_urls.txt"])
        
        assert result.exit_code == 0

    @patch('audioflow.cli.parse_urls_from_file')
    def test_batch_command_no_urls(self, mock_parse_urls):
        """Test batch command with no valid URLs"""
        mock_parse_urls.return_value = []
        
        runner = CliRunner()
        with runner.isolated_filesystem():
            with open("empty_urls.txt", "w") as f:
                f.write("# No URLs here\n")
            
            result = runner.invoke(cli, ["batch", "empty_urls.txt"])
        
        assert result.exit_code == 1
        assert "No valid URLs found" in result.output

    def test_batch_command_nonexistent_file(self):
        """Test batch command with nonexistent file"""
        runner = CliRunner()
        result = runner.invoke(cli, ["batch", "nonexistent.txt"])
        
        assert result.exit_code != 0

    @patch('audioflow.cli.parse_urls_from_file')
    @patch('audioflow.cli.AudioDownloader')
    @patch('audioflow.cli.asyncio.run')
    def test_batch_command_with_retry(self, mock_asyncio, mock_downloader_class, mock_parse_urls):
        """Test batch command with retry option"""
        mock_parse_urls.return_value = ["https://youtube.com/watch?v=test1"]
        
        # Mock batch result with failures
        mock_batch_result = Mock()
        mock_batch_result.successful = []
        mock_batch_result.failed = [Mock()]  # One failure
        mock_batch_result.total_requests = 1
        mock_batch_result.success_rate = 0.0
        mock_batch_result.total_time = 10.0
        
        # Mock retry result
        mock_retry_result = Mock()
        mock_retry_result.successful = [Mock()]  # Success on retry
        mock_retry_result.failed = []
        
        mock_downloader = Mock()
        mock_downloader.retry_failed_downloads.return_value = mock_retry_result
        mock_downloader_class.return_value = mock_downloader
        mock_asyncio.side_effect = [mock_batch_result, mock_retry_result]
        
        runner = CliRunner()
        with runner.isolated_filesystem():
            with open("test_urls.txt", "w") as f:
                f.write("https://youtube.com/watch?v=test1\n")
            
            result = runner.invoke(cli, ["batch", "test_urls.txt", "--retry"])
        
        assert result.exit_code == 0


class TestConfigCommand:
    """Tests for config command"""

    def test_config_show_command(self):
        """Test config show command"""
        runner = CliRunner()
        result = runner.invoke(cli, ["config"])
        
        assert result.exit_code == 0
        assert "AudioFlow Configuration" in result.output
        assert "Output Directory" in result.output
        assert "Audio Quality" in result.output


class TestInfoCommand:
    """Tests for info command"""

    def test_info_help(self):
        """Test info command help"""
        runner = CliRunner()
        result = runner.invoke(cli, ["info", "--help"])
        
        assert result.exit_code == 0
        assert "Get information about a URL" in result.output

    @patch('audioflow.cli.yt_dlp.YoutubeDL')
    def test_info_command_success(self, mock_ytdlp):
        """Test successful info command"""
        # Mock successful info extraction
        mock_info = {
            "title": "Test Video",
            "uploader": "Test Channel",
            "duration": 180,
            "view_count": 1000000,
            "upload_date": "20240101",
            "description": "Test description"
        }
        
        mock_instance = Mock()
        mock_instance.extract_info.return_value = mock_info
        mock_ytdlp.return_value.__enter__.return_value = mock_instance
        
        runner = CliRunner()
        result = runner.invoke(cli, ["info", "https://youtube.com/watch?v=test"])
        
        assert result.exit_code == 0
        assert "Test Video" in result.output

    @patch('audioflow.cli.yt_dlp.YoutubeDL')
    def test_info_command_failure(self, mock_ytdlp):
        """Test failed info command"""
        mock_instance = Mock()
        mock_instance.extract_info.side_effect = Exception("Failed to extract info")
        mock_ytdlp.return_value.__enter__.return_value = mock_instance
        
        runner = CliRunner()
        result = runner.invoke(cli, ["info", "https://youtube.com/watch?v=test"])
        
        assert result.exit_code == 1