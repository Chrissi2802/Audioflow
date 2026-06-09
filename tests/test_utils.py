"""Tests for utility functions"""

from pathlib import Path

import pytest

from audioflow.core.utils import (
    sanitize_filename,
    format_duration,
    format_file_size,
    validate_url,
    parse_urls_from_file,
    create_output_directory,
)


class TestSanitizeFilename:
    """Tests for sanitize_filename function"""

    def test_basic_sanitization(self):
        """Test basic filename sanitization"""
        assert sanitize_filename("normal_filename") == "normal_filename"
        assert sanitize_filename("file with spaces") == "file with spaces"

    def test_invalid_characters(self):
        """Test removal of invalid characters"""
        assert sanitize_filename('file<>:"/\\|?*name') == "file_name"
        assert sanitize_filename("file\x00\x1f\x7fname") == "filename"

    def test_multiple_underscores(self):
        """Test reduction of multiple underscores"""
        assert sanitize_filename("file___name") == "file_name"
        assert sanitize_filename("file____name") == "file_name"

    def test_leading_trailing_cleanup(self):
        """Test cleanup of leading/trailing dots and spaces"""
        assert sanitize_filename("  .file.  ") == "file."
        assert sanitize_filename("...file...") == "file"

    def test_empty_filename(self):
        """Test empty filename handling"""
        assert sanitize_filename("") == "untitled"
        assert sanitize_filename("   ") == "untitled"
        assert sanitize_filename("...") == "untitled"

    def test_unicode_normalization(self):
        """Test unicode normalization"""
        # This test might need adjustment based on actual behavior
        result = sanitize_filename("café")
        assert "caf" in result


class TestFormatDuration:
    """Tests for format_duration function"""

    def test_none_duration(self):
        """Test None duration"""
        assert format_duration(None) == "Unknown"

    def test_seconds_only(self):
        """Test duration less than a minute"""
        assert format_duration(30) == "00:30"
        assert format_duration(59) == "00:59"

    def test_minutes_and_seconds(self):
        """Test duration with minutes and seconds"""
        assert format_duration(90) == "01:30"
        assert format_duration(125) == "02:05"

    def test_hours_minutes_seconds(self):
        """Test duration with hours"""
        assert format_duration(3661) == "01:01:01"
        assert format_duration(7325) == "02:02:05"


class TestFormatFileSize:
    """Tests for format_file_size function"""

    def test_none_size(self):
        """Test None file size"""
        assert format_file_size(None) == "Unknown"

    def test_bytes(self):
        """Test file sizes in bytes"""
        assert format_file_size(500) == "500.0 B"
        assert format_file_size(1023) == "1023.0 B"

    def test_kilobytes(self):
        """Test file sizes in kilobytes"""
        assert format_file_size(1024) == "1.0 KB"
        assert format_file_size(1536) == "1.5 KB"

    def test_megabytes(self):
        """Test file sizes in megabytes"""
        assert format_file_size(1024 * 1024) == "1.0 MB"
        assert format_file_size(int(1.5 * 1024 * 1024)) == "1.5 MB"

    def test_gigabytes(self):
        """Test file sizes in gigabytes"""
        assert format_file_size(1024 * 1024 * 1024) == "1.0 GB"


class TestValidateUrl:
    """Tests for validate_url function"""

    def test_valid_urls(self):
        """Test valid URLs"""
        valid_urls = [
            "https://www.example.com",
            "http://example.com",
            "https://example.com/path",
            "https://example.com:8080/path",
            "https://subdomain.example.com",
        ]
        
        for url in valid_urls:
            assert validate_url(url), f"URL should be valid: {url}"

    def test_invalid_urls(self):
        """Test invalid URLs"""
        invalid_urls = [
            "not_a_url",
            "ftp://example.com",
            "example.com",
            "",
            "https://",
        ]
        
        for url in invalid_urls:
            assert not validate_url(url), f"URL should be invalid: {url}"


class TestParseUrlsFromFile:
    """Tests for parse_urls_from_file function"""

    def test_parse_valid_urls(self, sample_urls_file):
        """Test parsing URLs from file"""
        urls = parse_urls_from_file(sample_urls_file)
        
        # Should get 4 URLs (3 from sample_urls + 1 additional)
        assert len(urls) == 4
        assert "https://www.youtube.com/watch?v=dQw4w9WgXcQ" in urls

    def test_parse_nonexistent_file(self):
        """Test parsing from nonexistent file"""
        urls = parse_urls_from_file(Path("nonexistent.txt"))
        assert urls == []

    def test_parse_empty_file(self, temp_output_dir):
        """Test parsing from empty file"""
        empty_file = temp_output_dir / "empty.txt"
        empty_file.touch()
        
        urls = parse_urls_from_file(empty_file)
        assert urls == []

    def test_parse_file_with_comments(self, temp_output_dir):
        """Test parsing file with comments and blank lines"""
        test_file = temp_output_dir / "test.txt"
        with open(test_file, "w") as f:
            f.write("# This is a comment\n")
            f.write("\n")
            f.write("https://www.youtube.com/watch?v=test1\n")
            f.write("# Another comment\n")
            f.write("https://www.youtube.com/watch?v=test2\n")
            f.write("invalid_url\n")
        
        urls = parse_urls_from_file(test_file)
        assert len(urls) == 2
        assert "https://www.youtube.com/watch?v=test1" in urls
        assert "https://www.youtube.com/watch?v=test2" in urls


class TestCreateOutputDirectory:
    """Tests for create_output_directory function"""

    def test_create_simple_directory(self, temp_output_dir):
        """Test creating simple output directory"""
        output_path = temp_output_dir / "output"
        result_path = create_output_directory(output_path)
        
        assert result_path == output_path
        assert output_path.exists()
        assert output_path.is_dir()

    def test_create_artist_directory(self, temp_output_dir):
        """Test creating directory organized by artist"""
        output_path = temp_output_dir / "output"
        result_path = create_output_directory(
            output_path, organize_by_artist=True, artist="Test Artist"
        )
        
        expected_path = output_path / "Test Artist"
        assert result_path == expected_path
        assert expected_path.exists()
        assert expected_path.is_dir()

    def test_create_artist_directory_sanitized(self, temp_output_dir):
        """Test creating artist directory with sanitized name"""
        output_path = temp_output_dir / "output"
        result_path = create_output_directory(
            output_path, organize_by_artist=True, artist="Test/Artist<>"
        )
        
        # Artist name should be sanitized
        assert "Test_Artist_" in str(result_path)
        assert result_path.exists()

    def test_create_without_artist(self, temp_output_dir):
        """Test creating directory when organize by artist but no artist provided"""
        output_path = temp_output_dir / "output"
        result_path = create_output_directory(
            output_path, organize_by_artist=True, artist=None
        )
        
        assert result_path == output_path
        assert output_path.exists()

    def test_create_nested_directories(self, temp_output_dir):
        """Test creating nested directory structure"""
        nested_path = temp_output_dir / "level1" / "level2" / "level3"
        result_path = create_output_directory(nested_path)
        
        assert result_path == nested_path
        assert nested_path.exists()
        assert nested_path.is_dir()