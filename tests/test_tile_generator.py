"""
Tests for tile generation functionality.
"""

import json
import tempfile
import sqlite3
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
import pytest
import subprocess

from tilecraft.core.tile_generator import (
    TileGenerator,
    TileGenerationError,
    TippecanoeError,
    ValidationError,
    MemoryError
)
from tilecraft.models.config import (
    TilecraftConfig, BoundingBox, FeatureConfig, OutputConfig, 
    PaletteConfig, TileConfig, FeatureType
)
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
        tiles=TileConfig(min_zoom=8, max_zoom=14),
        _env_file=None  # Disable environment file loading for tests
    )


@pytest.fixture
def tile_generator(test_config, cache_manager):
    """Create tile generator instance."""
    return TileGenerator(test_config, cache_manager)


@pytest.fixture
def sample_geojson_files(temp_dir):
    """Create sample GeoJSON files for testing."""
    files = {}
    
    # Create rivers GeoJSON
    rivers_data = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[-104.5, 39.5], [-104.4, 39.6]]
                },
                "properties": {
                    "waterway": "river",
                    "name": "Test River"
                }
            }
        ]
    }
    
    rivers_path = temp_dir / "rivers.geojson"
    with open(rivers_path, 'w') as f:
        json.dump(rivers_data, f)
    files["rivers"] = rivers_path
    
    # Create forest GeoJSON
    forest_data = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[-104.6, 39.4], [-104.5, 39.4], [-104.5, 39.5], [-104.6, 39.5], [-104.6, 39.4]]]
                },
                "properties": {
                    "natural": "forest",
                    "name": "Test Forest"
                }
            }
        ]
    }
    
    forest_path = temp_dir / "forest.geojson"
    with open(forest_path, 'w') as f:
        json.dump(forest_data, f)
    files["forest"] = forest_path
    
    return files


@pytest.fixture
def sample_mbtiles(temp_dir):
    """Create sample MBTiles file for testing."""
    mbtiles_path = temp_dir / "test.mbtiles"
    
    # Create a minimal MBTiles database
    with sqlite3.connect(mbtiles_path) as conn:
        cursor = conn.cursor()
        
        # Create metadata table
        cursor.execute("""
            CREATE TABLE metadata (
                name TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        
        # Insert metadata
        cursor.execute("INSERT INTO metadata VALUES ('format', 'pbf')")
        cursor.execute("INSERT INTO metadata VALUES ('name', 'test')")
        cursor.execute("INSERT INTO metadata VALUES ('version', '1.0')")
        
        # Create tiles table
        cursor.execute("""
            CREATE TABLE tiles (
                zoom_level INTEGER,
                tile_column INTEGER,
                tile_row INTEGER,
                tile_data BLOB,
                PRIMARY KEY (zoom_level, tile_column, tile_row)
            )
        """)
        
        # Insert sample tile data
        cursor.execute("INSERT INTO tiles VALUES (8, 0, 0, ?)", (b'fake_tile_data',))
        cursor.execute("INSERT INTO tiles VALUES (9, 0, 0, ?)", (b'fake_tile_data_2',))
        
        conn.commit()
    
    return mbtiles_path


class TestTileGenerator:
    """Tests for tile generator."""
    
    def test_initialization(self, test_config, cache_manager):
        """Test tile generator initialization."""
        generator = TileGenerator(test_config, cache_manager)
        
        assert generator.config == test_config
        assert generator.cache_manager == cache_manager
        assert generator.output_dir == test_config.output.tiles_dir
        assert generator.temp_dir.exists()
        assert generator.processing_stats['start_time'] is None
        assert generator.processing_stats['retries'] == 0
    
    def test_initialization_without_cache(self, test_config):
        """Test tile generator initialization without cache manager."""
        generator = TileGenerator(test_config)
        
        assert generator.config == test_config
        assert generator.cache_manager is None
        assert generator.output_dir == test_config.output.tiles_dir
    
    @patch('subprocess.run')
    def test_validate_tippecanoe_success(self, mock_run, tile_generator):
        """Test successful tippecanoe validation."""
        mock_run.return_value = Mock(stdout="tippecanoe 1.36.0\n")
        
        # Should not raise exception
        tile_generator._validate_tippecanoe()
        
        mock_run.assert_called_once_with(
            ['tippecanoe', '--version'],
            check=True,
            capture_output=True,
            text=True,
            timeout=10
        )
    
    @patch('subprocess.run')
    def test_validate_tippecanoe_not_found(self, mock_run, tile_generator):
        """Test tippecanoe not found error."""
        mock_run.side_effect = FileNotFoundError()
        
        with pytest.raises(TippecanoeError, match="tippecanoe not found"):
            tile_generator._validate_tippecanoe()
    
    @patch('subprocess.run')
    def test_validate_tippecanoe_error(self, mock_run, tile_generator):
        """Test tippecanoe command error."""
        mock_run.side_effect = subprocess.CalledProcessError(1, ['tippecanoe'], stderr="command failed")
        
        with pytest.raises(TippecanoeError, match="Tippecanoe error"):
            tile_generator._validate_tippecanoe()
    
    def test_validate_input_files_success(self, tile_generator, sample_geojson_files):
        """Test successful input file validation."""
        # Should not raise exception
        result = tile_generator._validate_and_filter_input_files(sample_geojson_files)
        assert len(result) == 2
    
    def test_validate_input_files_missing_file(self, tile_generator, temp_dir):
        """Test validation with missing input file."""
        feature_files = {"rivers": temp_dir / "nonexistent.geojson"}
        
        with pytest.raises(TileGenerationError, match="Feature file not found"):
            tile_generator._validate_and_filter_input_files(feature_files)
    
    def test_validate_input_files_empty_file(self, tile_generator, temp_dir):
        """Test validation with empty input file."""
        empty_file = temp_dir / "empty.geojson"
        empty_file.touch()
        
        feature_files = {"rivers": empty_file}
        
        # Should filter out empty files
        result = tile_generator._validate_and_filter_input_files(feature_files)
        assert len(result) == 0
    
    def test_validate_input_files_invalid_json(self, tile_generator, temp_dir):
        """Test validation with invalid JSON file."""
        invalid_file = temp_dir / "invalid.geojson"
        with open(invalid_file, 'w') as f:
            f.write("invalid json content")
        
        feature_files = {"rivers": invalid_file}
        
        with pytest.raises(TileGenerationError, match="Invalid GeoJSON file"):
            tile_generator._validate_and_filter_input_files(feature_files)
    
    def test_validate_input_files_no_valid_files(self, tile_generator, temp_dir):
        """Test validation with no valid files."""
        empty_file = temp_dir / "empty.geojson"
        empty_file.touch()
        
        feature_files = {"rivers": empty_file}
        
        with pytest.raises(TileGenerationError, match="No valid feature files"):
            tile_generator._validate_and_filter_input_files(feature_files)
    
    def test_generate_cache_key(self, tile_generator, sample_geojson_files):
        """Test cache key generation."""
        cache_key = tile_generator._generate_cache_key(sample_geojson_files)
        
        assert isinstance(cache_key, str)
        assert len(cache_key) == 16  # SHA256 hash truncated to 16 chars
        
        # Same files should generate same key
        cache_key2 = tile_generator._generate_cache_key(sample_geojson_files)
        assert cache_key == cache_key2
    
    def test_generate_cache_key_different_files(self, tile_generator, sample_geojson_files, temp_dir):
        """Test cache key generation with different files."""
        cache_key1 = tile_generator._generate_cache_key(sample_geojson_files)
        
        # Create different file set
        different_files = {"water": temp_dir / "water.geojson"}
        different_files["water"].write_text('{"type": "FeatureCollection", "features": []}')
        
        cache_key2 = tile_generator._generate_cache_key(different_files)
        
        assert cache_key1 != cache_key2
    
    def test_build_tippecanoe_command_basic(self, tile_generator, sample_geojson_files, temp_dir):
        """Test basic tippecanoe command building."""
        output_path = temp_dir / "output.mbtiles"
        cmd = tile_generator._build_tippecanoe_command(sample_geojson_files, output_path, 0)
        
        assert cmd[0] == 'tippecanoe'
        assert '--minimum-zoom=8' in cmd
        assert '--maximum-zoom=14' in cmd
        assert '--buffer=64' in cmd
        assert '--force' in cmd
        assert '--output' in cmd
        assert str(output_path) in cmd
        
        # Check layer specifications
        assert '-L' in cmd
        # Check that layer specifications are present
        layer_specs = [cmd[i+1] for i, arg in enumerate(cmd) if arg == '-L']
        assert any('rivers:' in spec for spec in layer_specs)
        assert any('forest:' in spec for spec in layer_specs)
    
    def test_build_tippecanoe_command_with_bbox(self, tile_generator, sample_geojson_files, temp_dir):
        """Test tippecanoe command building with bounding box."""
        output_path = temp_dir / "output.mbtiles"
        cmd = tile_generator._build_tippecanoe_command(sample_geojson_files, output_path, 0)
        
        # Should include clipping bounding box
        expected_bbox = f'--clip-bounding-box={tile_generator.config.bbox.west},{tile_generator.config.bbox.south},{tile_generator.config.bbox.east},{tile_generator.config.bbox.north}'
        assert expected_bbox in cmd
    
    def test_build_tippecanoe_command_retry_attempt(self, tile_generator, sample_geojson_files, temp_dir):
        """Test tippecanoe command building for retry attempts."""
        output_path = temp_dir / "output.mbtiles"
        cmd = tile_generator._build_tippecanoe_command(sample_geojson_files, output_path, 1)
        
        # Should have more aggressive feature dropping for retries
        drop_rate_args = [arg for arg in cmd if arg.startswith('--drop-rate=')]
        assert len(drop_rate_args) == 1
        
        # Drop rate should be higher for retries
        drop_rate = float(drop_rate_args[0].split('=')[1])
        assert drop_rate > 2.5  # Default drop rate
    
    def test_parse_tippecanoe_progress(self, tile_generator):
        """Test tippecanoe progress parsing."""
        assert tile_generator._parse_tippecanoe_progress("Reading features from file") == "reading features"
        assert tile_generator._parse_tippecanoe_progress("Sorting features") == "sorting features"
        assert tile_generator._parse_tippecanoe_progress("Choosing a maxzoom") == "optimizing zoom levels"
        assert tile_generator._parse_tippecanoe_progress("Tile 100/1000") == "generating tiles"
        assert tile_generator._parse_tippecanoe_progress("Wrote output.mbtiles") == "finalizing output"
        assert tile_generator._parse_tippecanoe_progress("Other message") == "processing"
    
    def test_parse_tippecanoe_error(self, tile_generator):
        """Test tippecanoe error parsing."""
        assert "out of memory" in tile_generator._parse_tippecanoe_error("out of memory error").lower()
        assert "killed" in tile_generator._parse_tippecanoe_error("process killed").lower()
        assert "input file not found" in tile_generator._parse_tippecanoe_error("no such file error").lower()
        assert "invalid geojson" in tile_generator._parse_tippecanoe_error("invalid geojson format").lower()
        assert "empty" in tile_generator._parse_tippecanoe_error("empty input file").lower()
        
        # Test generic error
        generic_error = tile_generator._parse_tippecanoe_error("Some other error\nSecond line")
        assert generic_error == "Some other error"
    
    def test_validate_output_success(self, tile_generator, sample_mbtiles):
        """Test successful output validation."""
        # Should not raise exception
        tile_generator._validate_output(sample_mbtiles)
        
        # Check that statistics were updated
        assert tile_generator.processing_stats['tiles_generated'] > 0
        assert tile_generator.processing_stats['output_size_bytes'] > 0
    
    def test_validate_output_missing_file(self, tile_generator, temp_dir):
        """Test output validation with missing file."""
        missing_file = temp_dir / "missing.mbtiles"
        
        with pytest.raises(ValidationError, match="Output file not found"):
            tile_generator._validate_output(missing_file)
    
    def test_validate_output_empty_file(self, tile_generator, temp_dir):
        """Test output validation with empty file."""
        empty_file = temp_dir / "empty.mbtiles"
        empty_file.touch()
        
        with pytest.raises(ValidationError, match="Output file is empty"):
            tile_generator._validate_output(empty_file)
    
    def test_validate_output_invalid_database(self, tile_generator, temp_dir):
        """Test output validation with invalid database."""
        invalid_file = temp_dir / "invalid.mbtiles"
        invalid_file.write_text("not a sqlite database")
        
        with pytest.raises(ValidationError, match="SQLite validation failed"):
            tile_generator._validate_output(invalid_file)
    
    def test_validate_output_missing_tables(self, tile_generator, temp_dir):
        """Test output validation with missing required tables."""
        incomplete_file = temp_dir / "incomplete.mbtiles"
        
        with sqlite3.connect(incomplete_file) as conn:
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE dummy (id INTEGER)")
            conn.commit()
        
        with pytest.raises(ValidationError, match="Missing required tables"):
            tile_generator._validate_output(incomplete_file)
    
    def test_validate_output_no_tiles(self, tile_generator, temp_dir):
        """Test output validation with no tiles."""
        empty_tiles_file = temp_dir / "empty_tiles.mbtiles"
        
        with sqlite3.connect(empty_tiles_file) as conn:
            cursor = conn.cursor()
            
            # Create required tables but no tiles
            cursor.execute("CREATE TABLE metadata (name TEXT, value TEXT)")
            cursor.execute("INSERT INTO metadata VALUES ('format', 'pbf')")
            cursor.execute("CREATE TABLE tiles (zoom_level INTEGER, tile_column INTEGER, tile_row INTEGER, tile_data BLOB)")
            conn.commit()
        
        with pytest.raises(ValidationError, match="No tiles generated"):
            tile_generator._validate_output(empty_tiles_file)
    
    def test_get_tile_info_success(self, tile_generator, sample_mbtiles):
        """Test successful tile info retrieval."""
        info = tile_generator.get_tile_info(sample_mbtiles)
        
        assert 'metadata' in info
        assert 'tile_count' in info
        assert 'zoom_range' in info
        assert 'tiles_per_zoom' in info
        assert 'tile_sizes' in info
        assert 'file_info' in info
        
        assert info['tile_count'] == 2
        assert info['zoom_range']['min'] == 8
        assert info['zoom_range']['max'] == 9
        assert info['metadata']['format'] == 'pbf'
    
    def test_get_tile_info_error(self, tile_generator, temp_dir):
        """Test tile info retrieval with error."""
        invalid_file = temp_dir / "invalid.mbtiles"
        invalid_file.write_text("not a database")
        
        info = tile_generator.get_tile_info(invalid_file)
        assert 'error' in info
    
    def test_validate_tippecanoe_method(self, tile_generator):
        """Test validate_tippecanoe method."""
        with patch.object(tile_generator, '_validate_tippecanoe') as mock_validate:
            mock_validate.return_value = None
            assert tile_generator.validate_tippecanoe() is True
            
            mock_validate.side_effect = TippecanoeError("test error")
            assert tile_generator.validate_tippecanoe() is False
    
    def test_cleanup_temp_files(self, tile_generator):
        """Test temporary file cleanup."""
        # Create some temporary files
        temp_file = tile_generator.temp_dir / "test_file.tmp"
        temp_file.write_text("test content")
        
        temp_subdir = tile_generator.temp_dir / "subdir"
        temp_subdir.mkdir()
        (temp_subdir / "nested_file.tmp").write_text("nested content")
        
        # Cleanup
        tile_generator.cleanup_temp_files()
        
        # Check that files are cleaned up
        assert not temp_file.exists()
        assert not temp_subdir.exists()
    
    def test_get_processing_info(self, tile_generator):
        """Test processing info retrieval."""
        with patch.object(tile_generator, 'validate_tippecanoe', return_value=True):
            info = tile_generator.get_processing_info()
            
            assert 'tippecanoe_available' in info
            assert 'config' in info
            assert 'system' in info
            assert 'processing_stats' in info
            
            assert info['tippecanoe_available'] is True
            assert 'zoom_range' in info['config']
            assert 'available_memory_gb' in info['system']
    
    @patch('tilecraft.core.tile_generator.TileGenerator._generate_tiles_internal')
    def test_generate_with_cache_hit(self, mock_generate, tile_generator, sample_geojson_files, temp_dir):
        """Test tile generation with cache hit."""
        # Setup cached file
        cached_file = temp_dir / "cached.mbtiles"
        cached_file.write_text("cached content")
        
        # Mock cache manager
        tile_generator.cache_manager.get_cached_tiles = Mock(return_value=cached_file)
        
        # Mock tippecanoe validation
        with patch.object(tile_generator, '_validate_tippecanoe'):
            result = tile_generator.generate(sample_geojson_files)
        
        assert result == cached_file
        mock_generate.assert_not_called()
    
    @patch('tilecraft.core.tile_generator.TileGenerator._generate_tiles_internal')
    @patch('tilecraft.core.tile_generator.TileGenerator._validate_output')
    def test_generate_with_cache_miss(self, mock_validate, mock_generate, tile_generator, sample_geojson_files, temp_dir):
        """Test tile generation with cache miss."""
        # Setup output file
        output_file = temp_dir / "output.mbtiles"
        output_file.write_text("generated content")
        
        mock_generate.return_value = output_file
        
        # Mock cache manager
        tile_generator.cache_manager.get_cached_tiles = Mock(return_value=None)
        tile_generator.cache_manager.cache_tiles = Mock(return_value=output_file)
        
        # Mock tippecanoe validation
        with patch.object(tile_generator, '_validate_tippecanoe'):
            result = tile_generator.generate(sample_geojson_files)
        
        assert result == output_file
        mock_generate.assert_called_once()
        mock_validate.assert_called_once_with(output_file)
    
    def test_generate_no_input_files(self, tile_generator):
        """Test tile generation with no input files."""
        with pytest.raises(TileGenerationError, match="No feature files provided"):
            tile_generator.generate({})
    
    @patch('tilecraft.core.tile_generator.TileGenerator._generate_tiles_internal')
    def test_generate_with_retry_on_memory_error(self, mock_generate, tile_generator, sample_geojson_files):
        """Test tile generation with retry on memory error."""
        # First call raises MemoryError, second succeeds
        output_file = Path("test_output.mbtiles")
        mock_generate.side_effect = [MemoryError("Out of memory"), output_file]
        
        with patch.object(tile_generator, '_validate_tippecanoe'):
            with patch.object(tile_generator, '_validate_output'):
                with patch.object(tile_generator, '_cleanup_memory'):
                    result = tile_generator._generate_with_retry(sample_geojson_files)
        
        assert result == output_file
        assert mock_generate.call_count == 2  # Initial call + 1 retry
    
    @patch('tilecraft.core.tile_generator.TileGenerator._generate_tiles_internal')
    def test_generate_with_retry_exhausted(self, mock_generate, tile_generator, sample_geojson_files):
        """Test tile generation with all retries exhausted."""
        # All calls raise errors
        mock_generate.side_effect = [
            TippecanoeError("Error 1"),
            TippecanoeError("Error 2"),
            TippecanoeError("Error 3")
        ]
        
        with patch.object(tile_generator, '_validate_tippecanoe'):
            with pytest.raises(TileGenerationError, match="failed after 3 attempts"):
                tile_generator._generate_with_retry(sample_geojson_files)
        
        assert mock_generate.call_count == 3  # All retry attempts


class TestTileGeneratorIntegration:
    """Integration tests for tile generator."""
    
    @patch('subprocess.Popen')
    def test_execute_tippecanoe_with_progress_success(self, mock_popen, tile_generator):
        """Test tippecanoe execution with progress tracking."""
        # Mock process
        mock_process = Mock()
        mock_process.stdout.readline.side_effect = [
            "Reading features from file\n",
            "Sorting features\n",
            "Tile 1/10\n",
            "Wrote output.mbtiles\n",
            ""  # End of output
        ]
        mock_process.poll.return_value = 0  # Success
        mock_popen.return_value = mock_process
        
        # Mock progress
        mock_progress = Mock()
        mock_task_id = 1
        
        cmd = ['tippecanoe', '--output', 'test.mbtiles']
        
        result = tile_generator._execute_tippecanoe_with_progress(cmd, mock_progress, mock_task_id)
        
        assert result.returncode == 0
        assert "Reading features from file" in result.stdout
        
        # Check progress updates were called
        assert mock_progress.update.call_count >= 2
    
    @patch('subprocess.Popen')
    def test_execute_tippecanoe_with_progress_failure(self, mock_popen, tile_generator):
        """Test tippecanoe execution failure with progress tracking."""
        # Mock process
        mock_process = Mock()
        mock_process.stdout.readline.side_effect = [
            "Reading features from file\n",
            "Error: out of memory\n",
            ""  # End of output
        ]
        mock_process.poll.return_value = 1  # Error
        mock_popen.return_value = mock_process
        
        # Mock progress
        mock_progress = Mock()
        mock_task_id = 1
        
        cmd = ['tippecanoe', '--output', 'test.mbtiles']
        
        with pytest.raises(TippecanoeError, match="Tippecanoe failed"):
            tile_generator._execute_tippecanoe_with_progress(cmd, mock_progress, mock_task_id)
    
    def test_memory_monitoring_normal(self, tile_generator):
        """Test memory monitoring under normal conditions."""
        # Mock psutil
        with patch('psutil.virtual_memory') as mock_memory:
            mock_memory.return_value.percent = 50.0  # Normal memory usage
            
            mock_progress = Mock()
            mock_task_id = 1
            
            # Start monitoring (should run briefly)
            import threading
            import time
            
            stop_event = threading.Event()
            
            def monitor_wrapper():
                try:
                    # Override the while loop to stop after one iteration
                    original_sleep = time.sleep
                    time.sleep = lambda x: stop_event.set()
                    
                    tile_generator._monitor_memory(mock_progress, mock_task_id)
                except Exception:
                    pass
                finally:
                    time.sleep = original_sleep
            
            thread = threading.Thread(target=monitor_wrapper)
            thread.daemon = True
            thread.start()
            
            # Wait for thread to complete
            stop_event.wait(timeout=1)
            
            # Check that progress was updated
            mock_progress.update.assert_called()
    
    def test_memory_monitoring_high_usage(self, tile_generator):
        """Test memory monitoring with high memory usage."""
        with patch('psutil.virtual_memory') as mock_memory:
            mock_memory.return_value.percent = 96.0  # Critical memory usage
            
            mock_progress = Mock()
            mock_task_id = 1
            
            # Memory monitoring should raise MemoryError
            with pytest.raises(MemoryError, match="Critical memory usage"):
                # Run one iteration of memory monitoring
                import time
                original_sleep = time.sleep
                time.sleep = lambda x: None  # Skip sleep
                
                try:
                    tile_generator._monitor_memory(mock_progress, mock_task_id)
                finally:
                    time.sleep = original_sleep 