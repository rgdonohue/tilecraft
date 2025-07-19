"""
Tests for preview generation functionality.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from tilecraft.models.config import BoundingBox
from tilecraft.utils.preview import PreviewGenerator


class TestPreviewGenerator:
    """Tests for preview generator."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def preview_generator(self, temp_dir):
        """Create preview generator instance."""
        return PreviewGenerator(temp_dir / "preview")

    @pytest.fixture
    def test_mbtiles(self, temp_dir):
        """Create test MBTiles file."""
        mbtiles_path = temp_dir / "test.mbtiles"
        mbtiles_path.touch()
        return mbtiles_path

    @pytest.fixture
    def test_style(self, temp_dir):
        """Create test style file."""
        style_path = temp_dir / "style.json"
        style_data = {
            "version": 8,
            "sources": {
                "vector-source": {
                    "type": "vector",
                    "url": "test://example"
                }
            },
            "layers": []
        }
        with open(style_path, "w") as f:
            json.dump(style_data, f)
        return style_path

    @pytest.fixture
    def test_bbox(self):
        """Create test bounding box."""
        return BoundingBox(west=-105.0, south=39.0, east=-104.0, north=40.0)

    def test_initialization(self, temp_dir):
        """Test preview generator initialization."""
        output_dir = temp_dir / "preview"
        generator = PreviewGenerator(output_dir)
        
        assert generator.output_dir == output_dir
        assert output_dir.exists()

    def test_generate_html_preview(self, preview_generator, test_mbtiles, test_style, test_bbox):
        """Test HTML preview generation."""
        preview_path = preview_generator.generate_html_preview(
            test_mbtiles, test_style, test_bbox
        )
        
        assert preview_path.exists()
        assert preview_path.name == "preview.html"
        
        # Check that additional files were created
        assert (preview_generator.output_dir / "style.json").exists()
        assert (preview_generator.output_dir / "start_tile_server.py").exists()
        
        # Check HTML content
        html_content = preview_path.read_text()
        assert "Tilecraft Preview" in html_content
        assert "MapLibre GL" in html_content
        assert test_mbtiles.name in html_content

    def test_extract_bounds_fallback(self, preview_generator, test_mbtiles):
        """Test bounds extraction fallback."""
        bbox = preview_generator._extract_bounds_from_mbtiles(test_mbtiles)
        
        # Should return world bounds as fallback
        assert bbox.west == -180
        assert bbox.south == -85
        assert bbox.east == 180
        assert bbox.north == 85

    def test_copy_style_file(self, preview_generator, test_style):
        """Test style file copying and modification."""
        style_copy_path = preview_generator._copy_style_file(test_style)
        
        assert style_copy_path.exists()
        assert style_copy_path.name == "style.json"
        
        # Check that sources were modified for local server
        with open(style_copy_path, "r") as f:
            modified_style = json.load(f)
        
        vector_source = modified_style["sources"]["vector-source"]
        assert "localhost:8080" in vector_source["url"]

    def test_create_tile_server_script(self, preview_generator, test_mbtiles):
        """Test tile server script creation."""
        preview_generator._create_tile_server_script(test_mbtiles)
        
        server_script = preview_generator.output_dir / "start_tile_server.py"
        assert server_script.exists()
        
        # Check script content
        script_content = server_script.read_text()
        assert "Flask" in script_content
        assert "sqlite3" in script_content
        assert str(test_mbtiles.absolute()) in script_content
        
        # Check that it's executable
        assert server_script.stat().st_mode & 0o111  # Check execute bits

    def test_generate_without_bbox(self, preview_generator, test_mbtiles, test_style):
        """Test preview generation without explicit bbox."""
        preview_path = preview_generator.generate_html_preview(
            test_mbtiles, test_style
        )
        
        assert preview_path.exists()
        
        # Should work with fallback bounds
        html_content = preview_path.read_text()
        assert "center: [0" in html_content  # Should center on 0,0 roughly

    def test_static_map_not_implemented(self, preview_generator, test_mbtiles, test_style, test_bbox):
        """Test that static map generation returns None (not implemented)."""
        result = preview_generator.generate_static_map(
            test_mbtiles, test_style, (test_bbox.west, test_bbox.south, test_bbox.east, test_bbox.north)
        )
        
        assert result is None