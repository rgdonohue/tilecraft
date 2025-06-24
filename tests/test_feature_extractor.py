"""
Tests for feature extraction functionality.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

from tilecraft.core.feature_extractor import (
    FeatureExtractor, 
    OSMFeatureHandler, 
    FeatureExtractionError, 
    OSMProcessingError,
    GeometryValidationError
)
from tilecraft.models.config import FeatureType, TilecraftConfig, BoundingBox, FeatureConfig, OutputConfig, PaletteConfig
from tilecraft.utils.cache import CacheManager


@pytest.fixture
def temp_dir():
    """Create temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def cache_manager(temp_dir):
    """Create cache manager for testing."""
    cache_dir = temp_dir / "cache"
    return CacheManager(cache_dir, enabled=True)


@pytest.fixture
def test_config(temp_dir):
    """Create test configuration."""
    return TilecraftConfig(
        bbox=BoundingBox(west=-105.0, south=39.0, east=-104.0, north=40.0),
        features=FeatureConfig(types=[FeatureType.RIVERS, FeatureType.FOREST]),
        palette=PaletteConfig(name="test_palette"),
        output=OutputConfig(base_dir=temp_dir / "output"),
        _env_file=None  # Disable environment file loading for tests
    )


@pytest.fixture
def feature_extractor(test_config, cache_manager):
    """Create feature extractor instance."""
    return FeatureExtractor(test_config, cache_manager)


@pytest.fixture
def sample_osm_data(temp_dir):
    """Create sample OSM data file."""
    osm_content = """<?xml version="1.0" encoding="UTF-8"?>
<osm version="0.6" generator="test">
  <node id="1" lat="39.5" lon="-104.5">
    <tag k="waterway" v="river"/>
    <tag k="name" v="Test River"/>
  </node>
  <way id="2">
    <nd ref="1"/>
    <nd ref="3"/>
    <tag k="natural" v="forest"/>
  </way>
</osm>"""
    
    osm_path = temp_dir / "test.osm"
    with open(osm_path, 'w') as f:
        f.write(osm_content)
    
    return osm_path


class TestOSMFeatureHandler:
    """Tests for OSM feature handler."""
    
    def test_initialization(self):
        """Test handler initialization."""
        tag_filters = {'waterway': ['river', 'stream']}
        handler = OSMFeatureHandler(FeatureType.RIVERS, tag_filters)
        
        assert handler.feature_type == FeatureType.RIVERS
        assert handler.tag_filters == tag_filters
        assert handler.features == []
        assert handler.processed_count == 0
        assert handler.error_count == 0
    
    def test_matches_filters_exact_match(self):
        """Test tag matching with exact values."""
        tag_filters = {'waterway': ['river', 'stream']}
        handler = OSMFeatureHandler(FeatureType.RIVERS, tag_filters)
        
        # Mock tags
        mock_tags = Mock()
        mock_tags.__contains__ = Mock(return_value=True)
        mock_tags.__getitem__ = Mock(return_value='river')
        
        assert handler._matches_filters(mock_tags)
    
    def test_matches_filters_wildcard(self):
        """Test tag matching with wildcard."""
        tag_filters = {'building': ['*']}
        handler = OSMFeatureHandler(FeatureType.BUILDINGS, tag_filters)
        
        mock_tags = Mock()
        mock_tags.__contains__ = Mock(return_value=True)
        mock_tags.__getitem__ = Mock(return_value='residential')
        
        assert handler._matches_filters(mock_tags)
    
    def test_matches_filters_no_match(self):
        """Test tag matching with no match."""
        tag_filters = {'waterway': ['river']}
        handler = OSMFeatureHandler(FeatureType.RIVERS, tag_filters)
        
        mock_tags = Mock()
        mock_tags.__contains__ = Mock(return_value=False)
        
        assert not handler._matches_filters(mock_tags)
    
    def test_create_point_feature(self):
        """Test point feature creation."""
        handler = OSMFeatureHandler(FeatureType.RIVERS, {})
        
        # Mock node
        mock_node = Mock()
        mock_node.id = 123
        mock_node.location.valid.return_value = True
        mock_node.location.lon = -104.5
        mock_node.location.lat = 39.5
        mock_node.tags = {'waterway': 'river', 'name': 'Test River'}
        
        feature = handler._create_point_feature(mock_node)
        
        assert feature['type'] == 'Feature'
        assert feature['properties']['osm_id'] == 123
        assert feature['properties']['osm_type'] == 'node'
        assert feature['properties']['waterway'] == 'river'
        assert feature['geometry']['type'] == 'Point'
        assert feature['geometry']['coordinates'] == [-104.5, 39.5]
    
    def test_create_point_feature_invalid_location(self):
        """Test point feature creation with invalid location."""
        handler = OSMFeatureHandler(FeatureType.RIVERS, {})
        
        # Mock node with invalid location
        mock_node = Mock()
        mock_node.location.valid.return_value = False
        
        feature = handler._create_point_feature(mock_node)
        assert feature is None
    
    def test_determine_geometry_type_polygon(self):
        """Test polygon geometry type determination."""
        handler = OSMFeatureHandler(FeatureType.BUILDINGS, {})
        
        tags = {'building': 'residential'}
        is_closed = True
        
        geometry_type = handler._determine_geometry_type(tags, is_closed)
        assert geometry_type == "Polygon"
    
    def test_determine_geometry_type_linestring(self):
        """Test linestring geometry type determination."""
        handler = OSMFeatureHandler(FeatureType.ROADS, {})
        
        tags = {'highway': 'primary'}
        is_closed = False
        
        geometry_type = handler._determine_geometry_type(tags, is_closed)
        assert geometry_type == "LineString"
    
    def test_determine_geometry_type_explicit_area(self):
        """Test explicit area tag handling."""
        handler = OSMFeatureHandler(FeatureType.PARKS, {})
        
        tags = {'leisure': 'park', 'area': 'yes'}
        is_closed = True
        
        geometry_type = handler._determine_geometry_type(tags, is_closed)
        assert geometry_type == "Polygon"


class TestFeatureExtractor:
    """Tests for feature extractor."""
    
    def test_initialization(self, test_config, cache_manager):
        """Test extractor initialization."""
        extractor = FeatureExtractor(test_config, cache_manager)
        
        assert extractor.config == test_config
        assert extractor.cache_manager == cache_manager
        assert extractor.output_dir == test_config.output.data_dir
        assert extractor.temp_dir.exists()
    
    def test_feature_mappings(self, feature_extractor):
        """Test feature type mappings."""
        mappings = feature_extractor.feature_mappings
        
        assert FeatureType.RIVERS in mappings
        assert FeatureType.FOREST in mappings
        assert FeatureType.WATER in mappings
        assert FeatureType.BUILDINGS in mappings
        
        # Check river mappings
        river_mapping = mappings[FeatureType.RIVERS]
        assert 'waterway' in river_mapping
        assert 'river' in river_mapping['waterway']
        assert 'stream' in river_mapping['waterway']
    
    def test_get_tag_filters_basic(self, feature_extractor):
        """Test basic tag filter retrieval."""
        filters = feature_extractor._get_tag_filters(FeatureType.RIVERS)
        
        assert 'waterway' in filters
        assert 'river' in filters['waterway']
        assert 'stream' in filters['waterway']
    
    def test_get_tag_filters_with_custom_tags(self, temp_dir, cache_manager):
        """Test tag filters with custom tags."""
        # Create config with custom tags
        test_config = TilecraftConfig(
            bbox=BoundingBox(west=-105.0, south=39.0, east=-104.0, north=40.0),
            features=FeatureConfig(
                types=[FeatureType.RIVERS, FeatureType.FOREST],
                custom_tags={'rivers': ['waterway=canal', 'natural=water']}
            ),
            palette=PaletteConfig(name="test_palette"),
            output=OutputConfig(base_dir=temp_dir / "output"),
            _env_file=None
        )
        
        extractor = FeatureExtractor(test_config, cache_manager)
        filters = extractor._get_tag_filters(FeatureType.RIVERS)
        
        assert 'waterway' in filters
        assert 'canal' in filters['waterway']
        assert 'natural' in filters
        assert 'water' in filters['natural']
    
    def test_validate_osm_file_xml(self, temp_dir):
        """Test OSM XML file validation."""
        # Create valid OSM XML file
        osm_content = """<?xml version="1.0" encoding="UTF-8"?>
<osm version="0.6" generator="test">
  <node id="1" lat="39.5" lon="-104.5"/>
</osm>"""
        
        osm_path = temp_dir / "test.osm"
        with open(osm_path, 'w') as f:
            f.write(osm_content)
        
        config = TilecraftConfig(
            bbox=BoundingBox(west=-105.0, south=39.0, east=-104.0, north=40.0),
            features=FeatureConfig(types=[FeatureType.RIVERS]),
            palette=PaletteConfig(name="test_palette"),
            output=OutputConfig(base_dir=temp_dir / "output"),
            _env_file=None
        )
        cache_manager = CacheManager(temp_dir / "cache")
        extractor = FeatureExtractor(config, cache_manager)
        
        # Should not raise exception
        extractor._validate_osm_file(osm_path)
    
    def test_validate_osm_file_empty(self, temp_dir):
        """Test empty OSM file validation."""
        osm_path = temp_dir / "empty.osm"
        osm_path.touch()  # Create empty file
        
        config = TilecraftConfig(
            bbox=BoundingBox(west=-105.0, south=39.0, east=-104.0, north=40.0),
            features=FeatureConfig(types=[FeatureType.RIVERS]),
            palette=PaletteConfig(name="test_palette"),
            output=OutputConfig(base_dir=temp_dir / "output"),
            _env_file=None
        )
        cache_manager = CacheManager(temp_dir / "cache")
        extractor = FeatureExtractor(config, cache_manager)
        
        with pytest.raises(OSMProcessingError, match="OSM file is empty"):
            extractor._validate_osm_file(osm_path)
    
    def test_validate_osm_file_invalid_xml(self, temp_dir):
        """Test invalid OSM XML file validation."""
        osm_content = "invalid xml content"
        
        osm_path = temp_dir / "invalid.osm"
        with open(osm_path, 'w') as f:
            f.write(osm_content)
        
        config = TilecraftConfig(
            bbox=BoundingBox(west=-105.0, south=39.0, east=-104.0, north=40.0),
            features=FeatureConfig(types=[FeatureType.RIVERS]),
            palette=PaletteConfig(name="test_palette"),
            output=OutputConfig(base_dir=temp_dir / "output"),
            _env_file=None
        )
        cache_manager = CacheManager(temp_dir / "cache")
        extractor = FeatureExtractor(config, cache_manager)
        
        with pytest.raises(OSMProcessingError, match="Invalid OSM XML format"):
            extractor._validate_osm_file(osm_path)
    
    def test_validate_geojson_file_valid(self, temp_dir):
        """Test valid GeoJSON file validation."""
        geojson_data = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"name": "test"},
                    "geometry": {
                        "type": "Point",
                        "coordinates": [-104.5, 39.5]
                    }
                }
            ]
        }
        
        geojson_path = temp_dir / "test.geojson"
        with open(geojson_path, 'w') as f:
            json.dump(geojson_data, f)
        
        config = TilecraftConfig(
            bbox=BoundingBox(west=-105.0, south=39.0, east=-104.0, north=40.0),
            features=FeatureConfig(types=[FeatureType.RIVERS]),
            palette=PaletteConfig(name="test_palette"),
            output=OutputConfig(base_dir=temp_dir / "output"),
            _env_file=None
        )
        cache_manager = CacheManager(temp_dir / "cache")
        extractor = FeatureExtractor(config, cache_manager)
        
        # Should not raise exception
        extractor._validate_geojson_file(geojson_path)
    
    def test_validate_geojson_file_invalid_structure(self, temp_dir):
        """Test invalid GeoJSON structure validation."""
        geojson_data = {
            "type": "InvalidType",
            "features": []
        }
        
        geojson_path = temp_dir / "invalid.geojson"
        with open(geojson_path, 'w') as f:
            json.dump(geojson_data, f)
        
        config = TilecraftConfig(
            bbox=BoundingBox(west=-105.0, south=39.0, east=-104.0, north=40.0),
            features=FeatureConfig(types=[FeatureType.RIVERS]),
            palette=PaletteConfig(name="test_palette"),
            output=OutputConfig(base_dir=temp_dir / "output"),
            _env_file=None
        )
        cache_manager = CacheManager(temp_dir / "cache")
        extractor = FeatureExtractor(config, cache_manager)
        
        with pytest.raises(GeometryValidationError, match="GeoJSON must be a FeatureCollection"):
            extractor._validate_geojson_file(geojson_path)
    
    def test_count_features(self, temp_dir):
        """Test feature counting."""
        geojson_data = {
            "type": "FeatureCollection",
            "features": [
                {"type": "Feature", "properties": {}, "geometry": {"type": "Point", "coordinates": [0, 0]}},
                {"type": "Feature", "properties": {}, "geometry": {"type": "Point", "coordinates": [1, 1]}},
                {"type": "Feature", "properties": {}, "geometry": {"type": "Point", "coordinates": [2, 2]}}
            ]
        }
        
        geojson_path = temp_dir / "test.geojson"
        with open(geojson_path, 'w') as f:
            json.dump(geojson_data, f)
        
        config = TilecraftConfig(
            bbox=BoundingBox(west=-105.0, south=39.0, east=-104.0, north=40.0),
            features=FeatureConfig(types=[FeatureType.RIVERS]),
            palette=PaletteConfig(name="test_palette"),
            output=OutputConfig(base_dir=temp_dir / "output"),
            _env_file=None
        )
        cache_manager = CacheManager(temp_dir / "cache")
        extractor = FeatureExtractor(config, cache_manager)
        
        count = extractor._count_features(geojson_path)
        assert count == 3
    
    def test_count_features_invalid_file(self, temp_dir):
        """Test feature counting with invalid file."""
        config = TilecraftConfig(
            bbox=BoundingBox(west=-105.0, south=39.0, east=-104.0, north=40.0),
            features=FeatureConfig(types=[FeatureType.RIVERS]),
            palette=PaletteConfig(name="test_palette"),
            output=OutputConfig(base_dir=temp_dir / "output"),
            _env_file=None
        )
        cache_manager = CacheManager(temp_dir / "cache")
        extractor = FeatureExtractor(config, cache_manager)
        
        nonexistent_path = temp_dir / "nonexistent.geojson"
        count = extractor._count_features(nonexistent_path)
        assert count == 0
    
    @patch('osmium.apply')
    def test_extract_feature_type_success(self, mock_osmium_apply, feature_extractor, temp_dir):
        """Test successful feature extraction."""
        # Create mock OSM file
        osm_path = temp_dir / "test.osm"
        osm_path.touch()
        
        # Mock progress
        mock_progress = Mock()
        mock_task_id = 1
        
        # Mock osmium handler
        with patch('tilecraft.core.feature_extractor.OSMFeatureHandler') as mock_handler_class:
            mock_handler = Mock()
            mock_handler.features = [
                {
                    "type": "Feature",
                    "properties": {"waterway": "river"},
                    "geometry": {"type": "Point", "coordinates": [-104.5, 39.5]}
                }
            ]
            mock_handler.processed_count = 1
            mock_handler.error_count = 0
            mock_handler_class.return_value = mock_handler
            
            output_path = temp_dir / "rivers.geojson"
            
            result = feature_extractor._extract_feature_type(
                osm_path, FeatureType.RIVERS, output_path, mock_progress, mock_task_id
            )
            
            assert result == output_path
            assert output_path.exists()
            
            # Verify GeoJSON content
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert data['type'] == 'FeatureCollection'
            assert len(data['features']) == 1
            assert data['features'][0]['properties']['waterway'] == 'river'
    
    @patch('osmium.apply')
    def test_extract_feature_type_osmium_error(self, mock_osmium_apply, feature_extractor, temp_dir):
        """Test feature extraction with osmium error."""
        # Make osmium.apply raise an exception
        mock_osmium_apply.side_effect = Exception("OSM processing failed")
        
        osm_path = temp_dir / "test.osm"
        osm_path.touch()
        
        mock_progress = Mock()
        mock_task_id = 1
        
        output_path = temp_dir / "rivers.geojson"
        
        with pytest.raises(OSMProcessingError, match="OSM processing failed for rivers"):
            feature_extractor._extract_feature_type(
                osm_path, FeatureType.RIVERS, output_path, mock_progress, mock_task_id
            )
    
    def test_extract_missing_file(self, feature_extractor):
        """Test extraction with missing OSM file."""
        nonexistent_path = Path("/nonexistent/file.osm")
        
        with pytest.raises(FileNotFoundError, match="OSM data file not found"):
            feature_extractor.extract(nonexistent_path, [FeatureType.RIVERS])
    
    def test_get_extraction_info(self, feature_extractor):
        """Test extraction info retrieval."""
        feature_types = [FeatureType.RIVERS, FeatureType.FOREST]
        
        info = feature_extractor.get_extraction_info(feature_types)
        
        assert info['feature_types'] == ['rivers', 'forest']
        assert 'tag_mappings' in info
        assert 'rivers' in info['tag_mappings']
        assert 'forest' in info['tag_mappings']
        assert info['max_retries'] == feature_extractor.MAX_RETRIES
        assert info['cache_enabled'] == feature_extractor.cache_manager.enabled
    
    def test_cleanup_temp_files(self, feature_extractor):
        """Test temporary file cleanup."""
        # Create some temp files
        temp_file = feature_extractor.temp_dir / "test.geojson"
        temp_file.write_text('{"test": "data"}')
        
        assert temp_file.exists()
        
        feature_extractor.cleanup_temp_files()
        
        # File should be cleaned up
        assert not temp_file.exists()
    
    @patch('tilecraft.core.feature_extractor.FeatureExtractor._extract_feature_type_with_retry')
    def test_extract_with_cache_hit(self, mock_extract_retry, feature_extractor, temp_dir, sample_osm_data):
        """Test extraction with cache hit."""
        # Create cached GeoJSON file
        cached_geojson = {
            "type": "FeatureCollection",
            "features": [{"type": "Feature", "properties": {}, "geometry": {"type": "Point", "coordinates": [0, 0]}}]
        }
        
        bbox_str = feature_extractor.config.bbox.to_string()
        cached_path = feature_extractor.cache_manager.get_path(
            feature_extractor.cache_manager._get_cache_key(f"features_rivers_{bbox_str}"),
            ".geojson"
        )
        cached_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(cached_path, 'w') as f:
            json.dump(cached_geojson, f)
        
        result = feature_extractor.extract(sample_osm_data, [FeatureType.RIVERS])
        
        # Should use cached version, not call extraction
        mock_extract_retry.assert_not_called()
        assert FeatureType.RIVERS.value in result
        assert result[FeatureType.RIVERS.value] == cached_path
    
    @patch('tilecraft.core.feature_extractor.FeatureExtractor._extract_feature_type_with_retry')
    def test_extract_with_cache_miss(self, mock_extract_retry, feature_extractor, temp_dir, sample_osm_data):
        """Test extraction with cache miss."""
        # Setup mock return value
        output_path = temp_dir / "rivers.geojson"
        mock_extract_retry.return_value = output_path
        
        # Create the output file
        geojson_data = {
            "type": "FeatureCollection",
            "features": [{"type": "Feature", "properties": {}, "geometry": {"type": "Point", "coordinates": [0, 0]}}]
        }
        with open(output_path, 'w') as f:
            json.dump(geojson_data, f)
        
        result = feature_extractor.extract(sample_osm_data, [FeatureType.RIVERS])
        
        # Should call extraction
        mock_extract_retry.assert_called_once()
        assert FeatureType.RIVERS.value in result
        # Result should be the cached path, not the original output path
        assert result[FeatureType.RIVERS.value].exists()
        assert result[FeatureType.RIVERS.value].name.endswith('.geojson') 