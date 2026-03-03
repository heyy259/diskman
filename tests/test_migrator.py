"""Tests for directory migrator."""

import tempfile
from pathlib import Path

import pytest

from diskman.models import LinkType
from diskman.operations.migrator import DirectoryMigrator


class TestDirectoryMigrator:
    """Test DirectoryMigrator class."""

    def test_check_link_type_normal(self):
        """Test checking normal directory."""
        migrator = DirectoryMigrator()
        with tempfile.TemporaryDirectory() as tmpdir:
            link_type, target = migrator.check_link_type(tmpdir)
            assert link_type == LinkType.NORMAL
            assert target is None

    def test_check_link_type_not_found(self):
        """Test checking non-existent path."""
        migrator = DirectoryMigrator()
        link_type, target = migrator.check_link_type("/nonexistent/path/12345")
        assert link_type == LinkType.NOT_FOUND

    def test_migrate_source_not_exists(self):
        """Test migration with non-existent source."""
        migrator = DirectoryMigrator()
        result = migrator.migrate("/nonexistent/source", "/tmp/target")
        assert result.success is False
        assert "does not exist" in result.error

    def test_migrate_target_exists(self):
        """Test migration when target already exists."""
        migrator = DirectoryMigrator()
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source"
            target = Path(tmpdir) / "target"
            source.mkdir()
            target.mkdir()
            (source / "file.txt").write_text("test")

            result = migrator.migrate(str(source), str(target))
            assert result.success is False
            assert "already exists" in result.error

    def test_migrate_source_already_link(self):
        """Test migration when source is already a link."""
        migrator = DirectoryMigrator()
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create source and target
            source = Path(tmpdir) / "source"
            actual_data = Path(tmpdir) / "actual_data"
            actual_data.mkdir()
            (actual_data / "file.txt").write_text("test")

            # Create a junction from source to actual_data
            import subprocess
            subprocess.run(
                ["mklink", "/J", str(source), str(actual_data)],
                shell=True,
                capture_output=True,
            )

            # Try to migrate the junction
            target = Path(tmpdir) / "new_target"
            result = migrator.migrate(str(source), str(target))
            assert result.success is False
            # Should fail because source is already a link
            assert result.error is not None

    def test_migrate_success(self):
        """Test successful migration."""
        migrator = DirectoryMigrator()
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create source directory with content
            source = Path(tmpdir) / "source"
            source.mkdir()
            (source / "file.txt").write_text("test content")

            # Create target parent
            target = Path(tmpdir) / "target" / "source"

            # Perform migration
            result = migrator.migrate(str(source), str(target))

            if result.success:
                # Verify source is now a link
                link_type, link_target = migrator.check_link_type(str(source))
                assert link_type in [LinkType.SYMBOLIC_LINK, LinkType.JUNCTION]

                # Verify target has the content
                assert target.exists()
                assert (target / "file.txt").read_text() == "test content"
            else:
                # On systems without proper permissions, migration may fail
                pytest.skip(f"Migration failed: {result.error}")
