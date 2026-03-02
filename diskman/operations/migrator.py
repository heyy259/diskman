"""Directory migrator - migrate directories using symbolic links."""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from ..models import LinkType, MigrationResult


class DirectoryMigrator:
    """
    Migrator for moving directories and creating symbolic links.
    
    Handles the complete migration process:
    1. Copy directory to target location
    2. Verify copy success
    3. Delete original directory
    4. Create symbolic link
    """
    
    def check_link_type(self, path: str) -> tuple[LinkType, Optional[str]]:
        """Check if a path is a link."""
        if not os.path.exists(path):
            return LinkType.NOT_FOUND, None
        
        try:
            if os.path.islink(path):
                target = os.readlink(path)
                return LinkType.SYMBOLIC_LINK, target
            
            if os.name == 'nt':
                result = subprocess.run(
                    ["fsutil", "reparsepoint", "query", path],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                output = result.stdout
                
                if "Tag value: 0xa000000c" in output:
                    for line in output.split("\n"):
                        if "Print Name:" in line:
                            return LinkType.SYMBOLIC_LINK, line.split(":", 1)[1].strip()
                    return LinkType.SYMBOLIC_LINK, None
                
                if "Tag value: 0xa0000003" in output:
                    for line in output.split("\n"):
                        if "Print Name:" in line:
                            return LinkType.JUNCTION, line.split(":", 1)[1].strip()
                    return LinkType.JUNCTION, None
                    
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass
        
        return LinkType.NORMAL, None
    
    def migrate(
        self,
        source: str,
        target: str,
        verify: bool = True,
    ) -> MigrationResult:
        """
        Migrate a directory to a new location and create a symbolic link.
        
        Args:
            source: Source directory path
            target: Target directory path
            verify: Whether to verify copy before deleting source
            
        Returns:
            MigrationResult indicating success or failure
        """
        source_path = Path(source).expanduser().resolve()
        target_path = Path(target).expanduser().resolve()
        
        # Validate source
        if not source_path.exists():
            return MigrationResult(
                success=False,
                source=str(source_path),
                target=str(target_path),
                error=f"Source does not exist: {source_path}",
            )
        
        # Check if source is already a link
        link_type, _ = self.check_link_type(str(source_path))
        if link_type != LinkType.NORMAL:
            return MigrationResult(
                success=False,
                source=str(source_path),
                target=str(target_path),
                error=f"Source is already a {link_type.value}",
            )
        
        # Check if target exists
        if target_path.exists():
            return MigrationResult(
                success=False,
                source=str(source_path),
                target=str(target_path),
                error=f"Target already exists: {target_path}",
            )
        
        # Ensure target parent exists
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy directory
        try:
            if os.name == 'nt':
                # Use robocopy on Windows for better performance
                result = subprocess.run(
                    ["robocopy", str(source_path), str(target_path), "/E", "/R:1", "/W:1"],
                    capture_output=True,
                    timeout=3600,
                )
                # robocopy returns 0-7 for success
                if result.returncode > 7:
                    return MigrationResult(
                        success=False,
                        source=str(source_path),
                        target=str(target_path),
                        error=f"Copy failed with code {result.returncode}",
                    )
            else:
                # Use shutil on Unix
                shutil.copytree(source_path, target_path)
        except subprocess.TimeoutExpired:
            return MigrationResult(
                success=False,
                source=str(source_path),
                target=str(target_path),
                error="Copy timed out",
            )
        except Exception as e:
            return MigrationResult(
                success=False,
                source=str(source_path),
                target=str(target_path),
                error=f"Copy failed: {str(e)}",
            )
        
        # Verify copy
        if verify:
            if not target_path.exists():
                return MigrationResult(
                    success=False,
                    source=str(source_path),
                    target=str(target_path),
                    error="Copy verification failed: target not found",
                )
        
        # Delete source
        try:
            if os.name == 'nt':
                subprocess.run(
                    ["rmdir", "/s", "/q", str(source_path)],
                    shell=True,
                    capture_output=True,
                    timeout=300,
                )
            else:
                shutil.rmtree(source_path)
        except Exception as e:
            # Rollback: remove target if we can't delete source
            try:
                if os.name == 'nt':
                    subprocess.run(
                        ["rmdir", "/s", "/q", str(target_path)],
                        shell=True,
                        capture_output=True,
                        timeout=60,
                    )
                else:
                    shutil.rmtree(target_path)
            except Exception:
                pass
            
            return MigrationResult(
                success=False,
                source=str(source_path),
                target=str(target_path),
                error=f"Delete source failed: {str(e)}",
            )
        
        # Create symbolic link
        try:
            if os.name == 'nt':
                result = subprocess.run(
                    ["mklink", "/D", str(source_path), str(target_path)],
                    shell=True,
                    capture_output=True,
                    timeout=30,
                )
                if result.returncode != 0:
                    return MigrationResult(
                        success=False,
                        source=str(source_path),
                        target=str(target_path),
                        error=f"Create link failed: {result.stderr.decode() if result.stderr else 'unknown error'}",
                    )
            else:
                os.symlink(target_path, source_path)
        except Exception as e:
            return MigrationResult(
                success=False,
                source=str(source_path),
                target=str(target_path),
                error=f"Create link failed: {str(e)}",
            )
        
        # Verify link
        link_type, link_target = self.check_link_type(str(source_path))
        if link_type != LinkType.SYMBOLIC_LINK:
            return MigrationResult(
                success=False,
                source=str(source_path),
                target=str(target_path),
                error=f"Link verification failed: got {link_type.value}",
            )
        
        return MigrationResult(
            success=True,
            source=str(source_path),
            target=str(target_path),
            link_type="symbolic_link",
        )
    
    def convert_junction_to_symlink(
        self,
        path: str,
        target: Optional[str] = None,
    ) -> MigrationResult:
        """
        Convert a Windows Junction to a Symbolic Link.
        
        Args:
            path: Path to the junction
            target: Target path (if None, uses existing target)
            
        Returns:
            MigrationResult indicating success or failure
        """
        link_type, current_target = self.check_link_type(path)
        
        if link_type == LinkType.SYMBOLIC_LINK:
            return MigrationResult(
                success=True,
                source=path,
                target=current_target or "",
                link_type="symbolic_link",
            )
        
        if link_type != LinkType.JUNCTION:
            return MigrationResult(
                success=False,
                source=path,
                target=target or "",
                error=f"Path is not a junction: {link_type.value}",
            )
        
        # Use existing target if not specified
        actual_target = target or current_target
        if not actual_target:
            return MigrationResult(
                success=False,
                source=path,
                target="",
                error="Cannot determine target path",
            )
        
        # Remove junction (doesn't delete target)
        try:
            if os.name == 'nt':
                subprocess.run(
                    ["rmdir", path],
                    shell=True,
                    capture_output=True,
                    timeout=60,
                )
            else:
                os.rmdir(path)
        except Exception as e:
            return MigrationResult(
                success=False,
                source=path,
                target=actual_target,
                error=f"Remove junction failed: {str(e)}",
            )
        
        # Create symbolic link
        try:
            if os.name == 'nt':
                result = subprocess.run(
                    ["mklink", "/D", path, actual_target],
                    shell=True,
                    capture_output=True,
                    timeout=30,
                )
                if result.returncode != 0:
                    return MigrationResult(
                        success=False,
                        source=path,
                        target=actual_target,
                        error="Create symbolic link failed",
                    )
            else:
                os.symlink(actual_target, path)
        except Exception as e:
            return MigrationResult(
                success=False,
                source=path,
                target=actual_target,
                error=f"Create symbolic link failed: {str(e)}",
            )
        
        return MigrationResult(
            success=True,
            source=path,
            target=actual_target,
            link_type="symbolic_link",
        )
