"""Tests for directory analyzer."""


from diskman.analysis.analyzer import DirectoryAnalyzer
from diskman.models import (
    AnalysisContext,
    DirectoryInfo,
    DirectoryType,
    LinkType,
    RecommendedAction,
    RiskLevel,
)


class TestDirectoryAnalyzer:
    """Test DirectoryAnalyzer class."""

    def test_analyze_cache_directory(self):
        """Test analysis of cache directory."""
        analyzer = DirectoryAnalyzer()
        info = DirectoryInfo(
            path="/test/.cache",
            size_bytes=1024 * 1024,
            link_type=LinkType.NORMAL,
        )

        result = analyzer.analyze(info)
        assert result.directory_type == DirectoryType.CACHE
        assert result.risk_level == RiskLevel.LOW
        assert result.recommended_action == RecommendedAction.CAN_DELETE

    def test_analyze_migrated_directory(self):
        """Test analysis of migrated directory (symlink)."""
        analyzer = DirectoryAnalyzer()
        info = DirectoryInfo(
            path="/test/old_location",
            size_bytes=1024 * 1024,
            link_type=LinkType.SYMBOLIC_LINK,
            link_target="/new/location",
        )

        result = analyzer.analyze(info)
        assert result.directory_type == DirectoryType.MIGRATED
        assert result.risk_level == RiskLevel.SAFE
        assert result.recommended_action == RecommendedAction.KEEP
        assert "MIGRATED" in result.reason
        assert result.target_path == "/new/location"

    def test_analyze_junction(self):
        """Test analysis of junction."""
        analyzer = DirectoryAnalyzer()
        info = DirectoryInfo(
            path="/test/junction",
            size_bytes=1024 * 1024,
            link_type=LinkType.JUNCTION,
            link_target="D:\\data",
        )

        result = analyzer.analyze(info)
        assert result.directory_type == DirectoryType.MIGRATED
        assert result.risk_level == RiskLevel.SAFE

    def test_analyze_log_directory(self):
        """Test analysis of log directory."""
        analyzer = DirectoryAnalyzer()
        info = DirectoryInfo(
            path="/test/logs",
            size_bytes=1024 * 1024,
            link_type=LinkType.NORMAL,
        )

        result = analyzer.analyze(info)
        assert result.directory_type == DirectoryType.LOG
        assert result.risk_level == RiskLevel.LOW
        assert result.recommended_action == RecommendedAction.CAN_DELETE

    def test_analyze_config_directory(self):
        """Test analysis of config directory."""
        analyzer = DirectoryAnalyzer()
        info = DirectoryInfo(
            path="/test/.config",
            size_bytes=1024 * 1024,
            link_type=LinkType.NORMAL,
        )

        result = analyzer.analyze(info)
        assert result.directory_type == DirectoryType.CONFIG
        assert result.risk_level == RiskLevel.HIGH
        assert result.recommended_action == RecommendedAction.KEEP

    def test_analyze_build_directory(self):
        """Test analysis of build directory."""
        analyzer = DirectoryAnalyzer()
        info = DirectoryInfo(
            path="/test/build",
            size_bytes=1024 * 1024,
            link_type=LinkType.NORMAL,
        )

        result = analyzer.analyze(info)
        assert result.directory_type == DirectoryType.BUILD
        assert result.risk_level == RiskLevel.LOW
        assert result.recommended_action == RecommendedAction.CAN_DELETE

    def test_analyze_batch(self):
        """Test batch analysis."""
        analyzer = DirectoryAnalyzer()
        dirs = [
            DirectoryInfo(path="/test/cache", size_bytes=1024, link_type=LinkType.NORMAL),
            DirectoryInfo(path="/test/logs", size_bytes=1024, link_type=LinkType.NORMAL),
        ]

        results = analyzer.analyze_batch(dirs)
        assert len(results) == 2
        assert results[0].directory_type == DirectoryType.CACHE
        assert results[1].directory_type == DirectoryType.LOG

    def test_analyze_with_context_cleanup(self):
        """Test analysis with cleanup context."""
        analyzer = DirectoryAnalyzer()
        info = DirectoryInfo(
            path="/test/cache",
            size_bytes=1024 * 1024,
            link_type=LinkType.NORMAL,
        )
        context = AnalysisContext(intent="cleanup")

        result = analyzer.analyze(info, context)
        assert result.recommended_action == RecommendedAction.CAN_DELETE

    def test_analyze_with_context_migrate(self):
        """Test analysis with migration context."""
        analyzer = DirectoryAnalyzer()
        # Large project directory (project has action=KEEP, needed for migration)
        info = DirectoryInfo(
            path="/test/my_project",  # Contains 'project' in name -> PROJECT type
            size_bytes=1024 * 1024 * 600,  # 600 MB
            link_type=LinkType.NORMAL,
        )
        context = AnalysisContext(intent="migrate", target_drive="D:\\")

        result = analyzer.analyze(info, context)
        assert result.recommended_action == RecommendedAction.CAN_MOVE

    def test_analyze_unknown_directory(self):
        """Test analysis of unknown directory."""
        analyzer = DirectoryAnalyzer()
        info = DirectoryInfo(
            path="/test/some_random_dir_xyz",
            size_bytes=1024 * 1024,
            link_type=LinkType.NORMAL,
        )

        result = analyzer.analyze(info)
        # Unknown should require review
        assert result.recommended_action in [RecommendedAction.REVIEW, RecommendedAction.KEEP]
