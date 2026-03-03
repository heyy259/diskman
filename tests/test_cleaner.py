"""Tests for directory cleaner."""

import tempfile
from pathlib import Path

from diskman.operations.cleaner import DirectoryCleaner


class TestDirectoryCleaner:
    """Test DirectoryCleaner class."""

    def test_is_protected_home(self):
        """Test that home directory is protected."""
        cleaner = DirectoryCleaner()
        home = str(Path.home())
        assert cleaner.is_protected(home) is True

    def test_is_protected_custom(self):
        """Test custom protected paths."""
        cleaner = DirectoryCleaner(protected_paths=["/custom/protected"])
        assert cleaner.is_protected("/custom/protected") is True

    def test_get_size(self):
        """Test size calculation."""
        cleaner = DirectoryCleaner()
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "test.txt").write_text("x" * 1000)
            size = cleaner.get_size(tmpdir)
            assert size >= 1000

    def test_clean_nonexistent(self):
        """Test cleaning non-existent path."""
        cleaner = DirectoryCleaner()
        result = cleaner.clean("/nonexistent/path/12345")
        assert result.success is False
        assert "does not exist" in result.error

    def test_clean_dry_run(self):
        """Test dry run cleaning."""
        cleaner = DirectoryCleaner()
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "test.txt").write_text("test")
            (Path(tmpdir) / "subdir").mkdir()

            result = cleaner.clean(tmpdir, dry_run=True)
            assert result.success is True
            assert result.dry_run is True
            # Should not be deleted
            assert Path(tmpdir).exists()

    def test_clean_with_protected(self):
        """Test cleaning protected path."""
        cleaner = DirectoryCleaner()
        home = str(Path.home())

        result = cleaner.clean(home)
        assert result.success is False
        assert "protected" in result.error.lower()

    def test_clean_contents_dry_run(self):
        """Test cleaning contents dry run."""
        cleaner = DirectoryCleaner()
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "file1.txt").write_text("test")
            (Path(tmpdir) / "file2.log").write_text("test")

            result = cleaner.clean_contents(tmpdir, patterns=["*.log"], dry_run=True)
            assert result.success is True
            assert result.dry_run is True
            # Files should still exist
            assert (Path(tmpdir) / "file1.txt").exists()
            assert (Path(tmpdir) / "file2.log").exists()

    def test_clean_actual(self):
        """Test actual cleaning (with cleanup)."""
        cleaner = DirectoryCleaner()
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a temporary directory for testing
            test_dir = Path(tmpdir) / "to_clean"
            test_dir.mkdir()
            (test_dir / "file.txt").write_text("test")

            # Clean it (not dry run)
            result = cleaner.clean(str(test_dir), dry_run=False)
            assert result.success is True
            assert result.dry_run is False

    def test_clean_keep_root(self):
        """Test cleaning with keep_root option."""
        cleaner = DirectoryCleaner()
        with tempfile.TemporaryDirectory() as tmpdir:
            subdir = Path(tmpdir) / "subdir"
            subdir.mkdir()
            (subdir / "file.txt").write_text("test")

            result = cleaner.clean(tmpdir, dry_run=False, keep_root=True)
            assert result.success is True
            # Root should still exist but be empty
            assert Path(tmpdir).exists()
            assert len(list(Path(tmpdir).iterdir())) == 0

    def test_clean_contents_actual(self):
        """Test actual contents cleaning."""
        cleaner = DirectoryCleaner()
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "keep.txt").write_text("keep")
            (Path(tmpdir) / "delete.log").write_text("delete")

            result = cleaner.clean_contents(tmpdir, patterns=["*.log"], dry_run=False)
            assert result.success is True
            assert (Path(tmpdir) / "keep.txt").exists()
            assert not (Path(tmpdir) / "delete.log").exists()
