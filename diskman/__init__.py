"""
Diskman - AI-ready disk space analysis and management.

A modular tool for analyzing and managing disk space, designed for
both direct use and AI agent integration via MCP.
"""

from .models import (
    DirectoryInfo,
    AnalysisResult,
    ScanResult,
    MigrationResult,
    CleanResult,
    LinkType,
    RiskLevel,
    DirectoryType,
    RecommendedAction,
    AnalysisContext,
)
from .operations import DirectoryScanner, DirectoryMigrator, DirectoryCleaner
from .analysis import DirectoryAnalyzer

__version__ = "0.2.0"

__all__ = [
    # Models
    "DirectoryInfo",
    "AnalysisResult",
    "ScanResult",
    "MigrationResult",
    "CleanResult",
    "LinkType",
    "RiskLevel",
    "DirectoryType",
    "RecommendedAction",
    "AnalysisContext",
    # Operations
    "DirectoryScanner",
    "DirectoryMigrator",
    "DirectoryCleaner",
    # Analysis
    "DirectoryAnalyzer",
]
