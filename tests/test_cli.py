"""
Tests for the CLI interface.
"""

import pytest
from click.testing import CliRunner

from tilecraft.cli import main
from tilecraft.models.config import BoundingBox


class TestCLI:
    """Test suite for CLI functionality."""

    def test_help_command(self):
        """Test that help command works."""
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Tilecraft" in result.output
        assert "--bbox" in result.output
        assert "--features" in result.output
        assert "--palette" in result.output

    def test_version_command(self):
        """Test version command."""
        runner = CliRunner()
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output

    def test_missing_required_args(self):
        """Test error handling for missing required arguments."""
        runner = CliRunner()
        result = runner.invoke(main, [])
        assert result.exit_code != 0
        assert "Missing option" in result.output

    def test_invalid_bbox(self):
        """Test validation of invalid bounding box."""
        runner = CliRunner()
        result = runner.invoke(
            main, ["--bbox", "invalid", "--features", "rivers", "--palette", "test"]
        )
        assert result.exit_code != 0
        assert "Invalid bounding box" in result.output

    def test_invalid_bbox_order(self):
        """Test validation of bbox coordinate order."""
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "--bbox",
                "-105.0,40.0,-105.5,39.5",  # Invalid order
                "--features",
                "rivers",
                "--palette",
                "test",
            ],
        )
        assert result.exit_code != 0

    def test_valid_bbox_parsing(self):
        """Test valid bounding box parsing."""
        bbox_str = "-105.5,39.5,-105.0,40.0"
        bbox = BoundingBox.from_string(bbox_str)
        assert bbox.west == -105.5
        assert bbox.south == 39.5
        assert bbox.east == -105.0
        assert bbox.north == 40.0

    def test_invalid_features(self):
        """Test validation of invalid feature types."""
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "--bbox",
                "-105.5,39.5,-105.0,40.0",
                "--features",
                "invalid_feature",
                "--palette",
                "test",
            ],
        )
        assert result.exit_code != 0

    def test_zoom_level_validation(self):
        """Test zoom level validation."""
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "--bbox",
                "-105.5,39.5,-105.0,40.0",
                "--features",
                "rivers",
                "--palette",
                "test",
                "--min-zoom",
                "10",
                "--max-zoom",
                "5",  # Invalid: max < min
            ],
        )
        assert result.exit_code != 0
        assert "Maximum zoom must be >= minimum zoom" in result.output

    @pytest.mark.integration
    def test_full_command_structure(self, tmp_path):
        """Test full command with all options (without actual processing)."""
        # This would require mocking the pipeline
        pass
