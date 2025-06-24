"""
Pytest configuration and fixtures for Tilecraft tests.
"""

import tempfile
from pathlib import Path
from typing import Generator

import pytest
from tilecraft.models.config import (
    AIConfig,
    BoundingBox,
    FeatureConfig,
    FeatureType,
    OutputConfig,
    PaletteConfig,
    TilecraftConfig,
)


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Provide a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def sample_bbox() -> BoundingBox:
    """Provide a small test bounding box."""
    return BoundingBox(west=-105.5, south=39.5, east=-105.0, north=40.0)


@pytest.fixture
def sample_features() -> FeatureConfig:
    """Provide sample feature configuration."""
    return FeatureConfig(types=[FeatureType.RIVERS, FeatureType.FOREST])


@pytest.fixture
def sample_palette() -> PaletteConfig:
    """Provide sample palette configuration."""
    return PaletteConfig(name="test palette")


@pytest.fixture
def sample_config(temp_dir: Path, sample_bbox: BoundingBox, 
                  sample_features: FeatureConfig, sample_palette: PaletteConfig) -> TilecraftConfig:
    """Provide a complete test configuration."""
    return TilecraftConfig(
        bbox=sample_bbox,
        features=sample_features,
        palette=sample_palette,
        output=OutputConfig(base_dir=temp_dir / "output"),
        ai=AIConfig(api_key="test_key"),
        cache_enabled=False,  # Disable cache for tests
    )


@pytest.fixture
def sample_osm_data() -> str:
    """Provide minimal OSM XML data for testing."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<osm version="0.6" generator="test">
  <node id="1" lat="40.0" lon="-105.0"/>
  <node id="2" lat="40.1" lon="-105.1"/>
  <way id="1">
    <nd ref="1"/>
    <nd ref="2"/>
    <tag k="waterway" v="river"/>
    <tag k="name" v="Test River"/>
  </way>
</osm>"""


@pytest.fixture
def mock_ai_response() -> dict:
    """Provide mock AI response for testing."""
    return {
        "schema": {
            "name": "test_tileset",
            "layers": [
                {
                    "name": "rivers",
                    "geometry_type": "linestring",
                    "min_zoom": 0,
                    "max_zoom": 14,
                    "attributes": [
                        {"name": "name", "type": "string"},
                        {"name": "waterway", "type": "string"}
                    ]
                }
            ]
        },
        "style": {
            "version": 8,
            "name": "test_style",
            "sources": {},
            "layers": []
        }
    } 