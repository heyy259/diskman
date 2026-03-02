"""MCP Server for diskman."""

import os
from typing import Any, Optional

from fastmcp import FastMCP

from ..operations import DirectoryScanner, DirectoryMigrator, DirectoryCleaner
from ..analysis import DirectoryAnalyzer
from ..api.client import APIClient


def create_mcp_server() -> FastMCP:
    """Create and configure MCP server."""
    
    # Configuration
    api_url = os.getenv("DISKMAN_API_URL", "http://localhost:8765")
    api_key = os.getenv("DISKMAN_API_KEY")
    
    # Initialize components
    mcp = FastMCP("diskman")
    scanner = DirectoryScanner()
    migrator = DirectoryMigrator()
    cleaner = DirectoryCleaner()
    analyzer = DirectoryAnalyzer()
    api_client = APIClient(base_url=api_url, api_key=api_key)
    
    # === Local Tools (No external dependencies) ===
    
    @mcp.tool()
    def scan_directory(path: str) -> dict[str, Any]:
        """
        Scan a single directory and return size and link status.
        
        Args:
            path: Directory path to scan
            
        Returns:
            Directory information including size and link type
        """
        info = scanner.scan_directory(path)
        return info.to_dict()
    
    @mcp.tool()
    def scan_user_profile(
        base_path: Optional[str] = None,
        depth: int = 3,
    ) -> dict[str, Any]:
        """
        Scan user profile directory for all subdirectories.
        
        Args:
            base_path: Base path to scan (default: user home)
            depth: Scan depth (1-3)
            
        Returns:
            Scan results with all directories found
        """
        result = scanner.scan_user_profile(base_path, depth)
        return result.to_dict()
    
    @mcp.tool()
    def check_link_status(path: str) -> dict[str, Any]:
        """
        Check if a path is a symbolic link, junction, or normal directory.
        
        Args:
            path: Path to check
            
        Returns:
            Link type and target if applicable
        """
        link_type, target = scanner.check_link_type(path)
        return {
            "path": path,
            "link_type": link_type.value,
            "target": target,
        }
    
    @mcp.tool()
    def analyze_directory(
        path: str,
        user_context: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Analyze a directory and get recommendations.
        
        Uses built-in rules to determine if a directory can be
        safely deleted, should be moved, or should be kept.
        
        Args:
            path: Directory path to analyze
            user_context: Optional context (e.g., "Python developer")
            
        Returns:
            Analysis result with recommendations
        """
        from ..models import AnalysisContext
        
        # Scan directory
        info = scanner.scan_directory(path)
        
        # Create context
        context = None
        if user_context:
            context = AnalysisContext(
                user_type="developer" if "developer" in user_context.lower() else None,
            )
        
        # Analyze
        result = analyzer.analyze(info, context)
        return result.to_dict()
    
    @mcp.tool()
    def migrate_directory(
        source: str,
        target: str,
    ) -> dict[str, Any]:
        """
        Migrate a directory to another location using symbolic link.
        
        This operation:
        1. Copies the directory to the target location
        2. Deletes the original directory
        3. Creates a symbolic link from source to target
        
        WARNING: This modifies the file system. Backup important data first.
        
        Args:
            source: Source directory path
            target: Target directory path
            
        Returns:
            Migration result
        """
        result = migrator.migrate(source, target)
        return result.to_dict()
    
    @mcp.tool()
    def clean_directory(
        path: str,
        dry_run: bool = True,
    ) -> dict[str, Any]:
        """
        Clean a directory.
        
        Args:
            path: Directory path to clean
            dry_run: If True, only preview what would be deleted
            
        Returns:
            Clean result with space that would be freed
        """
        result = cleaner.clean(path, dry_run=dry_run)
        return result.to_dict()
    
    # === AI-Powered Tools (require API connection) ===
    
    @mcp.tool()
    async def analyze_with_ai(
        base_path: Optional[str] = None,
        user_context: Optional[str] = None,
        target_drive: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Scan and analyze directories using AI.
        
        Combines local scanning with AI-powered analysis for
        intelligent recommendations.
        
        Args:
            base_path: Base path to scan (default: user home)
            user_context: Context about the user (e.g., "Python developer")
            target_drive: Target drive for migration suggestions
            
        Returns:
            Analysis results with AI recommendations
        """
        # Step 1: Local scan
        scan_result = scanner.scan_user_profile(base_path)
        
        # Prepare data for AI
        directories = [
            {
                "path": d.path,
                "size_mb": d.size_mb,
                "link_type": d.link_type.value,
            }
            for d in scan_result.directories[:50]
        ]
        
        # Step 2: AI analysis
        try:
            ai_result = await api_client.analyze(
                directories=directories,
                user_context=user_context,
                target_drive=target_drive,
            )
            
            return {
                "scan_count": len(scan_result.directories),
                "total_size_mb": scan_result.total_size_mb,
                "ai_analysis": ai_result,
                "status": "success",
            }
        except Exception as e:
            # Fall back to local analysis
            local_results = [
                analyzer.analyze(d).to_dict()
                for d in scan_result.directories[:20]
            ]
            
            return {
                "scan_count": len(scan_result.directories),
                "total_size_mb": scan_result.total_size_mb,
                "local_analysis": local_results,
                "error": f"AI analysis failed: {str(e)}",
                "status": "partial",
            }
    
    @mcp.tool()
    async def get_ai_providers() -> list[dict[str, Any]]:
        """
        Get available AI providers and their status.
        
        Returns:
            List of provider information
        """
        try:
            return await api_client.get_providers()
        except Exception as e:
            return [{"error": str(e)}]
    
    return mcp


def run():
    """Run the MCP server."""
    mcp = create_mcp_server()
    mcp.run()


# For running directly
mcp = create_mcp_server()

if __name__ == "__main__":
    mcp.run()
