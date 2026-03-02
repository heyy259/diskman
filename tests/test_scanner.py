"""Tests for directory scanner."""

import os
import tempfile
import pytest
from pathlib import Path

from diskman.operations.scanner import DirectoryScanner
from diskman.models import LinkType


class TestDirectoryScanner:
    """Test DirectoryScanner class."""

    def test_check_link_type_normal(self):
        """Test checking normal directory."""
        scanner = DirectoryScanner()
        with tempfile.TemporaryDirectory() as tmpdir:
            link_type, target = scanner.check_link_type(tmpdir)
            assert link_type == LinkType.NORMAL
            assert target is None

    def test_check_link_type_not_found(self):
        """Test checking non-existent path."""
        scanner = DirectoryScanner()
        link_type, target = scanner.check_link_type("/nonexistent/path/12345")
        assert link_type == LinkType.NOT_FOUND

    def test_get_directory_size_empty(self):
        """Test size of empty directory."""
        scanner = DirectoryScanner()
        with tempfile.TemporaryDirectory() as tmpdir:
            size = scanner.get_directory_size(tmpdir)
            assert size == 0

    def test_get_directory_size_with_files(self):
        """Test size calculation with files."""
        scanner = DirectoryScanner()
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("Hello World")  # 11 bytes
            
            size = scanner.get_directory_size(tmpdir)
            assert size >= 11

    def test_get_file_types(self):
        """Test file type detection."""
        scanner = DirectoryScanner()
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files with different extensions
            (Path(tmpdir) / "test1.txt").write_text("test")
            (Path(tmpdir) / "test2.py").write_text("test")
            (Path(tmpdir) / "test3.txt").write_text("test")
            
            types = scanner.get_file_types(tmpdir)
            assert ".txt" in types
            assert types[".txt"] == 2
            assert ".py" in types
            assert types[".py"] == 1

    def test_count_files(self):
        """Test file counting."""
        scanner = DirectoryScanner()
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "file1.txt").write_text("test")
            (Path(tmpdir) / "file2.txt").write_text("test")
            (Path(tmpdir) / "file3.txt").write_text("test")
            
            count = scanner.count_files(tmpdir)
            assert count == 3

    def test_scan_directory(self):
        """Test single directory scan."""
        scanner = DirectoryScanner()
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "test.txt").write_text("Hello")
            
            info = scanner.scan_directory(tmpdir)
            assert info.path == tmpdir
            assert info.size_bytes > 0
            assert info.link_type == LinkType.NORMAL

    def test_scan_path(self):
        """Test path scanning with subdirectories."""
        scanner = DirectoryScanner()
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create structure
            subdir1 = Path(tmpdir) / "dir1"
            subdir2 = Path(tmpdir) / "dir2"
            subdir1.mkdir()
            subdir2.mkdir()
            
            (subdir1 / "file1.txt").write_text("x" * 1000)
            (subdir2 / "file2.txt").write_text("y" * 2000)
            
            result = scanner.scan_path(tmpdir, max_depth=1)
            assert len(result.directories) >= 2
            assert result.total_size_bytes > 0

    def test_scan_nonexistent(self):
        """Test scanning non-existent path."""
        scanner = DirectoryScanner()
        result = scanner.scan_path("/nonexistent/path")
        assert len(result.directories) == 0

    def test_scan_with_size_filter(self):
        """Test scanning with minimum size filter."""
        scanner = DirectoryScanner()
        with tempfile.TemporaryDirectory() as tmpdir:
            small = Path(tmpdir) / "small"
            large = Path(tmpdir) / "large"
            small.mkdir()
            large.mkdir()
            
            (small / "tiny.txt").write_text("x")
            (large / "big.txt").write_text("x" * 1024 * 1024)  # 1MB
            
            result = scanner.scan_path(tmpdir, min_size_mb=0.5)
            assert len(result.directories) == 1
            assert "large" in result.directories[0].path
