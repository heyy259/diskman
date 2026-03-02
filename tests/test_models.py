"""Tests for data models."""

import pytest
from diskman.models import (
    DirectoryInfo,
    ScanResult,
    AnalysisResult,
    MigrationResult,
    CleanResult,
    LinkType,
    DirectoryType,
    RiskLevel,
    RecommendedAction,
    AnalysisContext,
)


class TestDirectoryInfo:
    """Test DirectoryInfo model."""

    def test_creation(self):
        """Test basic creation."""
        info = DirectoryInfo(path="/test", size_bytes=1024)
        assert info.path == "/test"
        assert info.size_bytes == 1024
        assert info.link_type == LinkType.NORMAL

    def test_size_properties(self):
        """Test size conversion properties."""
        info = DirectoryInfo(path="/test", size_bytes=1024 * 1024 * 1024)  # 1 GB
        assert info.size_mb == 1024.0
        assert info.size_gb == 1.0

    def test_to_dict(self):
        """Test serialization."""
        info = DirectoryInfo(path="/test", size_bytes=1024)
        d = info.to_dict()
        assert d["path"] == "/test"
        assert d["size_bytes"] == 1024
        assert d["link_type"] == "normal"


class TestAnalysisResult:
    """Test AnalysisResult model."""

    def test_creation(self):
        """Test basic creation."""
        result = AnalysisResult(
            path="/test",
            directory_type=DirectoryType.CACHE,
            risk_level=RiskLevel.LOW,
            recommended_action=RecommendedAction.CAN_DELETE,
            reason="Test reason",
        )
        assert result.path == "/test"
        assert result.directory_type == DirectoryType.CACHE

    def test_migrated_type(self):
        """Test migrated directory type."""
        result = AnalysisResult(
            path="/test",
            directory_type=DirectoryType.MIGRATED,
            risk_level=RiskLevel.SAFE,
            recommended_action=RecommendedAction.KEEP,
            reason="Migrated",
            target_path="/new/location",
        )
        assert result.directory_type == DirectoryType.MIGRATED
        assert result.target_path == "/new/location"


class TestLinkType:
    """Test LinkType enum."""

    def test_all_types(self):
        """Test all link types exist."""
        assert LinkType.NORMAL.value == "normal"
        assert LinkType.SYMBOLIC_LINK.value == "symbolic_link"
        assert LinkType.JUNCTION.value == "junction"
        assert LinkType.NOT_FOUND.value == "not_found"


class TestRiskLevel:
    """Test RiskLevel enum."""

    def test_all_levels(self):
        """Test all risk levels exist."""
        assert RiskLevel.SAFE.value == "safe"
        assert RiskLevel.LOW.value == "low"
        assert RiskLevel.MEDIUM.value == "medium"
        assert RiskLevel.HIGH.value == "high"
        assert RiskLevel.CRITICAL.value == "critical"


class TestRecommendedAction:
    """Test RecommendedAction enum."""

    def test_all_actions(self):
        """Test all actions exist."""
        assert RecommendedAction.CAN_DELETE.value == "can_delete"
        assert RecommendedAction.CAN_MOVE.value == "can_move"
        assert RecommendedAction.KEEP.value == "keep"
        assert RecommendedAction.REVIEW.value == "review"


class TestAnalysisContext:
    """Test AnalysisContext model."""

    def test_creation(self):
        """Test basic creation."""
        ctx = AnalysisContext(
            user_type="developer",
            project_type="python",
            intent="cleanup",
            target_drive="D:\\",
        )
        assert ctx.user_type == "developer"
        assert ctx.project_type == "python"
        assert ctx.intent == "cleanup"
        assert ctx.target_drive == "D:\\"

    def test_optional_fields(self):
        """Test optional fields."""
        ctx = AnalysisContext()
        assert ctx.user_type is None
        assert ctx.project_type is None
