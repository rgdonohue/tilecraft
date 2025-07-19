"""
Integration tests for the complete Tilecraft pipeline.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from tilecraft.models.config import (
    TilecraftConfig, BoundingBox, FeatureConfig, 
    PaletteConfig, OutputConfig, TileConfig, FeatureType
)
from tilecraft.core.pipeline import TilecraftPipeline


@pytest.fixture
def temp_dir():
    """Create temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def test_config(temp_dir):
    """Create test configuration."""
    return TilecraftConfig(
        bbox=BoundingBox(west=-105.0, south=39.0, east=-104.0, north=40.0),
        features=FeatureConfig(types=[FeatureType.RIVERS, FeatureType.FOREST]),
        palette=PaletteConfig(name="test_palette"),
        output=OutputConfig(base_dir=temp_dir / "output"),
        tiles=TileConfig(min_zoom=8, max_zoom=12),
        _env_file=None  # Disable environment file loading for tests
    )


@pytest.fixture
def sample_osm_data(temp_dir):
    """Create sample OSM data file."""
    osm_file = temp_dir / "sample.osm"
    osm_content = """<?xml version="1.0" encoding="UTF-8"?>
<osm version="0.6">
  <way id="1">
    <nd ref="1"/>
    <nd ref="2"/>
    <tag k="waterway" v="river"/>
    <tag k="name" v="Test River"/>
  </way>
  <way id="2">
    <nd ref="3"/>
    <nd ref="4"/>
    <nd ref="5"/>
    <nd ref="3"/>
    <tag k="natural" v="forest"/>
    <tag k="name" v="Test Forest"/>
  </way>
  <node id="1" lat="39.1" lon="-104.9"/>
  <node id="2" lat="39.2" lon="-104.8"/>
  <node id="3" lat="39.1" lon="-104.7"/>
  <node id="4" lat="39.2" lon="-104.7"/>
  <node id="5" lat="39.2" lon="-104.6"/>
</osm>"""
    with open(osm_file, 'w') as f:
        f.write(osm_content)
    return osm_file


@pytest.fixture
def sample_feature_files(temp_dir):
    """Create sample GeoJSON feature files."""
    files = {}
    
    # Rivers
    rivers_data = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[-104.9, 39.1], [-104.8, 39.2]]
                },
                "properties": {
                    "waterway": "river",
                    "name": "Test River"
                }
            }
        ]
    }
    
    rivers_file = temp_dir / "rivers.geojson"
    with open(rivers_file, 'w') as f:
        json.dump(rivers_data, f)
    files["rivers"] = rivers_file
    
    # Forest
    forest_data = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[-104.7, 39.1], [-104.7, 39.2], [-104.6, 39.2], [-104.7, 39.1]]]
                },
                "properties": {
                    "natural": "forest",
                    "name": "Test Forest"
                }
            }
        ]
    }
    
    forest_file = temp_dir / "forest.geojson"
    with open(forest_file, 'w') as f:
        json.dump(forest_data, f)
    files["forest"] = forest_file
    
    return files


class TestTilecraftIntegration:
    """Integration tests for the complete pipeline."""
    
    @patch('tilecraft.core.osm_downloader.OSMDownloader.download')
    @patch('tilecraft.core.feature_extractor.FeatureExtractor.extract')
    @patch('tilecraft.core.tile_generator.TileGenerator.generate')
    @patch('tilecraft.ai.schema_generator.SchemaGenerator.generate')
    @patch('tilecraft.ai.style_generator.StyleGenerator.generate')
    def test_pipeline_integration(self, mock_style_gen, mock_schema_gen, mock_tile_gen, 
                                mock_feature_extract, mock_osm_download,
                                test_config, sample_osm_data, sample_feature_files, temp_dir):
        """Test complete pipeline integration with mocked components."""
        
        # Setup mocks
        mock_osm_download.return_value = sample_osm_data
        mock_feature_extract.return_value = sample_feature_files
        
        # Mock tile generation
        tiles_file = temp_dir / "output.mbtiles"
        tiles_file.write_bytes(b"fake mbtiles data")
        mock_tile_gen.return_value = tiles_file
        
        # Mock schema generation
        mock_schema = {
            "layers": {
                "rivers": {"geometry": "LineString"},
                "forest": {"geometry": "Polygon"}
            }
        }
        mock_schema_gen.return_value = mock_schema
        
        # Mock style generation
        style_file = temp_dir / "style.json"
        style_file.write_text('{"version": 8}')
        mock_style_gen.return_value = style_file
        
        # Run pipeline
        pipeline = TilecraftPipeline(test_config)
        result = pipeline.run()
        
        # Verify results
        assert result["osm_data"] == sample_osm_data
        assert result["features"] == sample_feature_files
        assert result["schema"] == mock_schema
        assert result["tiles"] == tiles_file
        assert result["style"] == style_file
        
        # Verify mocks were called
        mock_osm_download.assert_called_once()
        mock_feature_extract.assert_called_once()
        mock_tile_gen.assert_called_once_with(sample_feature_files)
        mock_schema_gen.assert_called_once()
        mock_style_gen.assert_called_once()
        
        # Verify schema was saved
        schema_file = test_config.output.data_dir / "schema.json"
        assert schema_file.exists()
        with open(schema_file) as f:
            saved_schema = json.load(f)
        assert saved_schema == mock_schema
    
    def test_pipeline_initialization(self, test_config):
        """Test pipeline initialization creates all components."""
        pipeline = TilecraftPipeline(test_config)
        
        assert pipeline.config == test_config
        assert pipeline.cache_manager is not None
        assert pipeline.osm_downloader is not None
        assert pipeline.feature_extractor is not None
        assert pipeline.tile_generator is not None
        assert pipeline.schema_generator is not None
        assert pipeline.style_generator is not None
        
        # Verify output directories were created
        assert test_config.output.tiles_dir.exists()
        assert test_config.output.styles_dir.exists()
        assert test_config.output.data_dir.exists()
        assert test_config.output.cache_dir.exists()
    
    @patch('tilecraft.core.osm_downloader.OSMDownloader.download')
    def test_pipeline_osm_download_error(self, mock_osm_download, test_config):
        """Test pipeline handles OSM download errors."""
        mock_osm_download.side_effect = Exception("Download failed")
        
        pipeline = TilecraftPipeline(test_config)
        
        with pytest.raises(Exception, match="Download failed"):
            pipeline.run()
    
    @patch('tilecraft.core.osm_downloader.OSMDownloader.download')
    @patch('tilecraft.core.feature_extractor.FeatureExtractor.extract')
    def test_pipeline_feature_extraction_error(self, mock_feature_extract, mock_osm_download,
                                            test_config, sample_osm_data):
        """Test pipeline handles feature extraction errors."""
        mock_osm_download.return_value = sample_osm_data
        mock_feature_extract.side_effect = Exception("Extraction failed")
        
        pipeline = TilecraftPipeline(test_config)
        
        with pytest.raises(Exception, match="Extraction failed"):
            pipeline.run()
    
    @patch('tilecraft.core.osm_downloader.OSMDownloader.download')
    @patch('tilecraft.core.feature_extractor.FeatureExtractor.extract')
    @patch('tilecraft.core.tile_generator.TileGenerator.generate')
    def test_pipeline_tile_generation_error(self, mock_tile_gen, mock_feature_extract, 
                                          mock_osm_download, test_config, sample_osm_data, 
                                          sample_feature_files):
        """Test pipeline handles tile generation errors."""
        mock_osm_download.return_value = sample_osm_data
        mock_feature_extract.return_value = sample_feature_files
        mock_tile_gen.side_effect = Exception("Tile generation failed")
        
        pipeline = TilecraftPipeline(test_config)
        
        with pytest.raises(Exception, match="Tile generation failed"):
            pipeline.run()