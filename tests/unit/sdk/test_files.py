"""Tests for sdk.files module."""

import hashlib
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from sdk.files import compute_md5


class TestComputeMd5:
    """Tests for compute_md5 function."""
    
    def test_empty_file(self, tmp_path):
        """MD5 of empty file should match expected hash."""
        test_file = tmp_path / "empty.txt"
        test_file.write_text("")
        
        result = compute_md5(test_file)
        expected = hashlib.md5(b"").hexdigest()  # noqa: S324
        
        assert result == expected
    
    def test_simple_content(self, tmp_path):
        """MD5 of simple content should match expected hash."""
        test_file = tmp_path / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)
        
        result = compute_md5(test_file)
        expected = hashlib.md5(content).hexdigest()  # noqa: S324
        
        assert result == expected
    
    def test_large_file(self, tmp_path):
        """MD5 of large file should handle chunked reading correctly."""
        test_file = tmp_path / "large.bin"
        # Create 3MB of data (larger than chunk size of 1MB)
        content = b"x" * (3 * 1024 * 1024)
        test_file.write_bytes(content)
        
        result = compute_md5(test_file)
        expected = hashlib.md5(content).hexdigest()  # noqa: S324
        
        assert result == expected
    
    def test_binary_content(self, tmp_path):
        """MD5 of binary content should work correctly."""
        test_file = tmp_path / "binary.bin"
        content = bytes(range(256))
        test_file.write_bytes(content)
        
        result = compute_md5(test_file)
        expected = hashlib.md5(content).hexdigest()  # noqa: S324
        
        assert result == expected
    
    def test_file_not_found(self, tmp_path):
        """Should raise FileNotFoundError for non-existent file."""
        non_existent = tmp_path / "does_not_exist.txt"
        
        with pytest.raises(FileNotFoundError):
            compute_md5(non_existent)
    
    @patch("pathlib.Path.open", mock_open(read_data=b"test content"))
    def test_file_reading_mocked(self):
        """Test with mocked file to verify reading logic."""
        result = compute_md5(Path("/fake/path.txt"))
        expected = hashlib.md5(b"test content").hexdigest()  # noqa: S324
        
        assert result == expected
    
    def test_unicode_content(self, tmp_path):
        """MD5 of unicode content should work correctly."""
        test_file = tmp_path / "unicode.txt"
        content = "Hello, 世界! 🌍".encode("utf-8")
        test_file.write_bytes(content)
        
        result = compute_md5(test_file)
        expected = hashlib.md5(content).hexdigest()  # noqa: S324
        
        assert result == expected
