"""
Production-ready vector tile generation using tippecanoe with comprehensive error handling.
"""

import hashlib
import json
import logging
import os
import psutil
import shutil
import sqlite3
import subprocess
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import concurrent.futures

from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn, TaskID

from tilecraft.models.config import TilecraftConfig, FeatureType
from tilecraft.utils.cache import CacheManager

logger = logging.getLogger(__name__)


class TileGenerationError(Exception):
    """Base exception for tile generation errors."""
    pass


class TippecanoeError(TileGenerationError):
    """Exception for tippecanoe execution errors."""
    pass


class ValidationError(TileGenerationError):
    """Exception for output validation errors."""
    pass


class MemoryError(TileGenerationError):
    """Exception for memory-related errors."""
    pass


class TileGenerator:
    """Production-ready vector tile generator using tippecanoe."""
    
    # Processing configuration
    MAX_RETRIES = 3
    BASE_RETRY_DELAY = 5.0  # seconds
    MAX_RETRY_DELAY = 60.0  # seconds
    DEFAULT_TIMEOUT = 3600  # 1 hour for large datasets
    MEMORY_CHECK_INTERVAL = 10.0  # seconds
    MAX_MEMORY_USAGE_PCT = 85  # Maximum memory usage percentage
    
    # Tippecanoe output patterns for progress tracking
    PROGRESS_PATTERNS = [
        "For layer",
        "Reading features from",
        "Sorting",
        "Choosing a maxzoom",
        "Tile",
        "Created",
        "Wrote"
    ]
    
    def __init__(self, config: TilecraftConfig, cache_manager: Optional[CacheManager] = None):
        """
        Initialize tile generator.
        
        Args:
            config: Tilecraft configuration
            cache_manager: Optional cache manager instance
        """
        self.config = config
        self.cache_manager = cache_manager
        self.output_dir = config.output.tiles_dir
        
        # Create temp directory for processing
        self.temp_dir = Path(tempfile.gettempdir()) / "tilecraft" / "tiles"
        if config.tiles.temp_dir:
            self.temp_dir = config.tiles.temp_dir
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Memory monitoring
        self.process = psutil.Process()
        self.memory_warnings = 0
        
        # Statistics tracking
        self.processing_stats = {
            'start_time': None,
            'end_time': None,
            'input_files': 0,
            'input_size_bytes': 0,
            'output_size_bytes': 0,
            'features_processed': 0,
            'tiles_generated': 0,
            'memory_peak_mb': 0,
            'retries': 0
        }
    
    def generate(self, feature_files: Dict[str, Path]) -> Path:
        """
        Generate vector tiles from feature GeoJSON files.
        
        Args:
            feature_files: Dictionary mapping feature type to GeoJSON file path
            
        Returns:
            Path to generated and validated MBTiles file
            
        Raises:
            TileGenerationError: Tile generation failures
            TippecanoeError: Tippecanoe execution errors
            ValidationError: Output validation errors
        """
        if not feature_files:
            raise TileGenerationError("No feature files provided for tile generation")
        
        # Validate tippecanoe availability
        self._validate_tippecanoe()
        
        # Validate input files
        self._validate_input_files(feature_files)
        
        # Check cache first
        cache_key = self._generate_cache_key(feature_files)
        if self.cache_manager:
            cached_path = self.cache_manager.get_cached_tiles(cache_key)
            if cached_path and cached_path.exists():
                logger.info(f"Using cached tiles: {cached_path}")
                return cached_path
        
        logger.info(f"Generating vector tiles from {len(feature_files)} feature files")
        self._log_input_statistics(feature_files)
        
        # Start processing statistics
        self.processing_stats['start_time'] = datetime.now()
        self.processing_stats['input_files'] = len(feature_files)
        
        # Generate tiles with retry logic
        output_path = self._generate_with_retry(feature_files)
        
        # Validate output
        self._validate_output(output_path)
        
        # Cache result
        if self.cache_manager:
            try:
                cached_path = self.cache_manager.cache_tiles(cache_key, output_path)
                output_path = cached_path
            except Exception as e:
                logger.warning(f"Failed to cache tiles: {e}")
        
        # Finalize statistics
        self.processing_stats['end_time'] = datetime.now()
        self._log_processing_statistics(output_path)
        
        return output_path
    
    def _validate_tippecanoe(self) -> None:
        """
        Validate tippecanoe availability and version.
        
        Raises:
            TippecanoeError: Tippecanoe not available or invalid version
        """
        try:
            result = subprocess.run(
                ['tippecanoe', '--version'],
                check=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            version = result.stdout.strip()
            logger.debug(f"Using tippecanoe version: {version}")
            
            # Check for minimum version requirements if needed
            # This is a placeholder for version checking logic
            
        except subprocess.TimeoutExpired:
            raise TippecanoeError("Tippecanoe version check timed out")
        except subprocess.CalledProcessError as e:
            raise TippecanoeError(f"Tippecanoe error: {e.stderr}")
        except FileNotFoundError:
            raise TippecanoeError(
                "tippecanoe not found. Please install tippecanoe: "
                "https://github.com/felt/tippecanoe#installation"
            )
    
    def _validate_input_files(self, feature_files: Dict[str, Path]) -> None:
        """
        Validate input GeoJSON files.
        
        Args:
            feature_files: Feature files to validate
            
        Raises:
            TileGenerationError: Invalid input files
        """
        for feature_type, file_path in feature_files.items():
            if not file_path.exists():
                raise TileGenerationError(f"Feature file not found: {file_path}")
            
            if file_path.stat().st_size == 0:
                logger.warning(f"Empty feature file: {feature_type} ({file_path})")
                continue
            
            # Basic GeoJSON validation
            try:
                with open(file_path, 'r') as f:
                    # Read first few lines to validate JSON structure
                    content = f.read(1000)
                    if not content.strip().startswith('{'):
                        raise TileGenerationError(f"Invalid GeoJSON format: {file_path}")
                    
                    # Try to parse the beginning as JSON
                    json.loads(content + '}' if not content.rstrip().endswith('}') else content)
                    
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                raise TileGenerationError(f"Invalid GeoJSON file {file_path}: {e}")
            except Exception as e:
                logger.warning(f"Could not fully validate {file_path}: {e}")
    
    def _generate_cache_key(self, feature_files: Dict[str, Path]) -> str:
        """
        Generate cache key for tile generation.
        
        Args:
            feature_files: Input feature files
            
        Returns:
            Cache key string
        """
        # Create hash from file paths, modification times, and config
        hash_content = []
        
        # Add file information
        for feature_type, file_path in sorted(feature_files.items()):
            if file_path.exists():
                stat = file_path.stat()
                hash_content.append(f"{feature_type}:{file_path}:{stat.st_size}:{stat.st_mtime}")
        
        # Add relevant configuration
        config_items = [
            f"bbox:{self.config.bbox.to_string()}",
            f"min_zoom:{self.config.tiles.min_zoom}",
            f"max_zoom:{self.config.tiles.max_zoom}",
            f"buffer:{self.config.tiles.buffer}",
            f"quality:{self.config.tiles.quality_profile}",
            f"layers:{sorted(feature_files.keys())}"
        ]
        hash_content.extend(config_items)
        
        # Generate hash
        content_str = '|'.join(hash_content)
        return hashlib.sha256(content_str.encode()).hexdigest()[:16]
    
    def _generate_with_retry(self, feature_files: Dict[str, Path]) -> Path:
        """
        Generate tiles with retry logic and exponential backoff.
        
        Args:
            feature_files: Input feature files
            
        Returns:
            Path to generated MBTiles file
        """
        last_exception = None
        
        for attempt in range(self.MAX_RETRIES):
            try:
                if attempt > 0:
                    delay = min(self.BASE_RETRY_DELAY * (2 ** (attempt - 1)), self.MAX_RETRY_DELAY)
                    logger.info(f"Retrying tile generation (attempt {attempt + 1}/{self.MAX_RETRIES}) after {delay}s...")
                    time.sleep(delay)
                    self.processing_stats['retries'] += 1
                
                return self._generate_tiles_internal(feature_files, attempt)
                
            except MemoryError as e:
                logger.error(f"Memory error during tile generation (attempt {attempt + 1}): {e}")
                last_exception = e
                # Clear memory and try with more conservative settings
                self._cleanup_memory()
                continue
                
            except TippecanoeError as e:
                logger.error(f"Tippecanoe error (attempt {attempt + 1}): {e}")
                last_exception = e
                # Check if it's a recoverable error
                if "out of memory" in str(e).lower() or "killed" in str(e).lower():
                    self._cleanup_memory()
                    continue
                elif attempt == self.MAX_RETRIES - 1:
                    break
                continue
                
            except Exception as e:
                logger.error(f"Unexpected error during tile generation (attempt {attempt + 1}): {e}")
                last_exception = e
                if attempt == self.MAX_RETRIES - 1:
                    break
                continue
        
        # All retries failed
        raise TileGenerationError(f"Tile generation failed after {self.MAX_RETRIES} attempts: {last_exception}")
    
    def _generate_tiles_internal(self, feature_files: Dict[str, Path], attempt: int) -> Path:
        """
        Internal method to generate tiles with progress tracking.
        
        Args:
            feature_files: Input feature files
            attempt: Current attempt number
            
        Returns:
            Path to generated MBTiles file
        """
        # Determine output filename
        project_name = self.config.output.name or "tileset"
        output_path = self.output_dir / f"{project_name}.mbtiles"
        
        # Create temporary output path for atomic operation
        temp_output = self.temp_dir / f"{project_name}_{int(time.time())}.mbtiles"
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Build tippecanoe command
        cmd = self._build_tippecanoe_command(feature_files, temp_output, attempt)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=None if not self.config.verbose else None
        ) as progress:
            
            # Create progress tasks
            main_task = progress.add_task("Initializing tile generation...", total=None)
            memory_task = progress.add_task("Memory usage: 0%", total=100)
            
            # Start memory monitoring
            monitor_future = None
            if attempt == 0:  # Only monitor on first attempt to avoid overhead
                executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
                monitor_future = executor.submit(self._monitor_memory, progress, memory_task)
            
            try:
                # Execute tippecanoe with real-time output parsing
                result = self._execute_tippecanoe_with_progress(cmd, progress, main_task)
                
                # Stop memory monitoring
                if monitor_future:
                    monitor_future.cancel()
                    executor.shutdown(wait=False)
                
                # Move temporary file to final location
                if temp_output.exists():
                    shutil.move(str(temp_output), str(output_path))
                    progress.update(main_task, description="Tile generation complete")
                else:
                    raise TippecanoeError("Tippecanoe completed but output file not found")
                
                return output_path
                
            except Exception as e:
                # Cleanup on error
                if monitor_future:
                    monitor_future.cancel()
                    executor.shutdown(wait=False)
                if temp_output.exists():
                    temp_output.unlink()
                raise e
    
    def _build_tippecanoe_command(self, feature_files: Dict[str, Path], output_path: Path, attempt: int) -> List[str]:
        """
        Build optimized tippecanoe command with feature-specific settings.
        
        Args:
            feature_files: Input feature files
            output_path: Output MBTiles path
            attempt: Current attempt number for optimization
            
        Returns:
            Command arguments list
        """
        cmd = ['tippecanoe']
        
        # Basic zoom settings
        cmd.extend([
            f'--minimum-zoom={self.config.tiles.min_zoom}',
            f'--maximum-zoom={self.config.tiles.max_zoom}',
            f'--buffer={self.config.tiles.buffer}',
        ])
        
        # Get quality settings
        quality_settings = self.config.tiles.get_quality_settings()
        
        # Apply quality-based settings (more conservative on retries)
        if attempt > 0:
            # More conservative settings for retries
            cmd.extend([
                f'--drop-rate={quality_settings["drop_rate"] * (1.5 ** attempt)}',
                f'--simplification={quality_settings["simplification"] * (1.2 ** attempt)}',
            ])
        else:
            cmd.extend([
                f'--drop-rate={quality_settings["drop_rate"]}',
                f'--simplification={quality_settings["simplification"]}',
            ])
        
        # Feature and tile limits
        if quality_settings.get("no_feature_limit", True):
            cmd.append('--no-feature-limit')
        elif self.config.tiles.force_feature_limit:
            cmd.append(f'--feature-limit={self.config.tiles.force_feature_limit}')
        
        if quality_settings.get("no_tile_size_limit", True):
            cmd.append('--no-tile-size-limit')
        elif self.config.tiles.maximum_tile_bytes:
            cmd.append(f'--maximum-tile-bytes={self.config.tiles.maximum_tile_bytes}')
        
        # Advanced options
        if self.config.tiles.maximum_tile_features:
            cmd.append(f'--maximum-tile-features={self.config.tiles.maximum_tile_features}')
        
        if self.config.tiles.simplification_at_max_zoom > 0:
            cmd.append(f'--simplification-at-maximum-zoom={self.config.tiles.simplification_at_max_zoom}')
        
        # Layer-specific configurations
        for feature_type, geojson_path in feature_files.items():
            layer_config = self.config.tiles.get_layer_config(feature_type)
            
            # Add layer with specific zoom range
            layer_min_zoom = layer_config.get('min_zoom', self.config.tiles.min_zoom)
            layer_max_zoom = layer_config.get('max_zoom', self.config.tiles.max_zoom)
            
            cmd.extend([
                f'--layer={feature_type}',
                f'--minimum-zoom-for-layer={feature_type}:{layer_min_zoom}',
                f'--maximum-zoom-for-layer={feature_type}:{layer_max_zoom}',
                str(geojson_path)
            ])
        
        # Output options
        cmd.extend([
            '--force',  # Overwrite existing file
            '--quiet',  # Reduce verbose output for parsing
            '--progress-interval=1',  # Progress updates every second
            '--output', str(output_path)
        ])
        
        # Add bounding box if specified
        if self.config.bbox:
            bbox = self.config.bbox
            cmd.append(f'--clip-bounding-box={bbox.west},{bbox.south},{bbox.east},{bbox.north}')
        
        # Performance optimizations for large datasets
        available_memory_gb = psutil.virtual_memory().available // (1024**3)
        if available_memory_gb >= 8:
            cmd.append('--read-parallel')
        
        return cmd
    
    def _execute_tippecanoe_with_progress(self, cmd: List[str], progress: Progress, task_id: TaskID) -> subprocess.CompletedProcess:
        """
        Execute tippecanoe with real-time progress parsing.
        
        Args:
            cmd: Command to execute
            progress: Progress tracker
            task_id: Progress task ID
            
        Returns:
            Completed process result
        """
        logger.debug(f"Executing: {' '.join(cmd)}")
        progress.update(task_id, description="Starting tippecanoe...")
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            output_lines = []
            current_stage = "initializing"
            
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                
                if output:
                    line = output.strip()
                    output_lines.append(line)
                    
                    # Parse progress information
                    stage = self._parse_tippecanoe_progress(line)
                    if stage != current_stage:
                        current_stage = stage
                        progress.update(task_id, description=f"Tippecanoe: {stage}")
                    
                    # Log important messages
                    if any(pattern in line for pattern in ["Error", "Warning", "Created"]):
                        logger.debug(f"Tippecanoe: {line}")
            
            # Wait for process completion
            return_code = process.poll()
            
            if return_code != 0:
                error_output = '\n'.join(output_lines[-10:])  # Last 10 lines
                error_msg = self._parse_tippecanoe_error(error_output)
                raise TippecanoeError(f"Tippecanoe failed (exit code {return_code}): {error_msg}")
            
            # Success
            result = subprocess.CompletedProcess(
                cmd, return_code, 
                stdout='\n'.join(output_lines),
                stderr=None
            )
            
            logger.debug(f"Tippecanoe completed successfully")
            return result
            
        except subprocess.TimeoutExpired:
            if process:
                process.kill()
            raise TippecanoeError(f"Tippecanoe timed out after {self.DEFAULT_TIMEOUT} seconds")
        except Exception as e:
            if process:
                process.kill()
            raise TippecanoeError(f"Error executing tippecanoe: {e}")
    
    def _parse_tippecanoe_progress(self, line: str) -> str:
        """Parse tippecanoe output for progress information."""
        line_lower = line.lower()
        
        if "reading features" in line_lower:
            return "reading features"
        elif "sorting" in line_lower:
            return "sorting features"
        elif "choosing a maxzoom" in line_lower:
            return "optimizing zoom levels"
        elif "tile " in line_lower and "/" in line:
            return "generating tiles"
        elif "wrote" in line_lower:
            return "finalizing output"
        else:
            return "processing"
    
    def _parse_tippecanoe_error(self, error_output: str) -> str:
        """Parse tippecanoe error output for meaningful messages."""
        if "out of memory" in error_output.lower():
            return "Out of memory - try reducing dataset size or using a machine with more RAM"
        elif "killed" in error_output.lower():
            return "Process was killed - likely due to memory constraints"
        elif "no such file" in error_output.lower():
            return "Input file not found"
        elif "invalid geojson" in error_output.lower():
            return "Invalid GeoJSON format in input file"
        elif "empty" in error_output.lower():
            return "Empty input file or no features to process"
        else:
            # Return first meaningful line
            lines = [line.strip() for line in error_output.split('\n') if line.strip()]
            return lines[0] if lines else "Unknown tippecanoe error"
    
    def _monitor_memory(self, progress: Progress, task_id: TaskID) -> None:
        """Monitor memory usage during processing."""
        try:
            while True:
                time.sleep(self.MEMORY_CHECK_INTERVAL)
                
                # Get system memory info
                memory = psutil.virtual_memory()
                memory_pct = memory.percent
                
                # Update progress
                progress.update(task_id, completed=min(int(memory_pct), 100))
                
                # Track peak memory
                if memory_pct > self.processing_stats['memory_peak_mb']:
                    self.processing_stats['memory_peak_mb'] = memory_pct
                
                # Warning if memory usage is high
                if memory_pct > self.MAX_MEMORY_USAGE_PCT:
                    self.memory_warnings += 1
                    if self.memory_warnings == 1:  # Only log first warning
                        logger.warning(f"High memory usage: {memory_pct:.1f}%")
                    
                    if memory_pct > 95:  # Critical memory usage
                        raise MemoryError(f"Critical memory usage: {memory_pct:.1f}%")
                        
        except Exception:
            # Memory monitoring should not crash the main process
            pass
    
    def _cleanup_memory(self) -> None:
        """Attempt to free memory before retry."""
        import gc
        gc.collect()
        
        # Clear any cached data
        if hasattr(self, '_temp_files'):
            for temp_file in self._temp_files:
                if temp_file.exists():
                    temp_file.unlink()
            self._temp_files.clear()
        
        logger.info("Memory cleanup completed")
    
    def _validate_output(self, output_path: Path) -> None:
        """
        Comprehensive validation of generated MBTiles file.
        
        Args:
            output_path: Path to MBTiles file to validate
            
        Raises:
            ValidationError: Output validation failures
        """
        if not output_path.exists():
            raise ValidationError(f"Output file not found: {output_path}")
        
        if output_path.stat().st_size == 0:
            raise ValidationError(f"Output file is empty: {output_path}")
        
        try:
            # Validate SQLite database structure
            with sqlite3.connect(output_path) as conn:
                cursor = conn.cursor()
                
                # Check required tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = {row[0] for row in cursor.fetchall()}
                
                required_tables = {'metadata', 'tiles'}
                missing_tables = required_tables - tables
                if missing_tables:
                    raise ValidationError(f"Missing required tables: {missing_tables}")
                
                # Validate metadata
                cursor.execute("SELECT name, value FROM metadata")
                metadata = dict(cursor.fetchall())
                
                if 'format' not in metadata:
                    raise ValidationError("Missing format in metadata")
                if metadata['format'] != 'pbf':
                    logger.warning(f"Unexpected tile format: {metadata['format']}")
                
                # Check tile count
                cursor.execute("SELECT COUNT(*) FROM tiles")
                tile_count = cursor.fetchone()[0]
                
                if tile_count == 0:
                    raise ValidationError("No tiles generated")
                
                # Validate zoom levels
                cursor.execute("SELECT MIN(zoom_level), MAX(zoom_level) FROM tiles")
                min_zoom, max_zoom = cursor.fetchone()
                
                if min_zoom is None or max_zoom is None:
                    raise ValidationError("Invalid zoom levels in tiles")
                
                if min_zoom < self.config.tiles.min_zoom:
                    logger.warning(f"Generated tiles include zoom {min_zoom} below configured minimum {self.config.tiles.min_zoom}")
                
                if max_zoom > self.config.tiles.max_zoom:
                    logger.warning(f"Generated tiles include zoom {max_zoom} above configured maximum {self.config.tiles.max_zoom}")
                
                # Sample tile validation
                cursor.execute("SELECT tile_data FROM tiles LIMIT 1")
                sample_tile = cursor.fetchone()
                if not sample_tile or not sample_tile[0]:
                    raise ValidationError("Invalid tile data found")
                
                # Update statistics
                self.processing_stats['tiles_generated'] = tile_count
                self.processing_stats['output_size_bytes'] = output_path.stat().st_size
                
                logger.info(f"Generated {tile_count} tiles, zoom levels {min_zoom}-{max_zoom}")
                
        except sqlite3.Error as e:
            raise ValidationError(f"SQLite validation failed: {e}")
        except Exception as e:
            raise ValidationError(f"Output validation failed: {e}")
    
    def _log_input_statistics(self, feature_files: Dict[str, Path]) -> None:
        """Log statistics about input files."""
        total_size = 0
        total_features = 0
        
        for feature_type, file_path in feature_files.items():
            if file_path.exists():
                size = file_path.stat().st_size
                total_size += size
                
                # Estimate feature count (very rough)
                try:
                    with open(file_path, 'r') as f:
                        content = f.read(10000)  # Sample
                        feature_count = content.count('"type": "Feature"')
                        if feature_count > 0:
                            # Extrapolate based on sample
                            estimated_total = int((feature_count * size) / len(content))
                            total_features += estimated_total
                            logger.debug(f"{feature_type}: ~{estimated_total:,} features, {size:,} bytes")
                except Exception:
                    logger.debug(f"{feature_type}: {size:,} bytes")
        
        self.processing_stats['input_size_bytes'] = total_size
        self.processing_stats['features_processed'] = total_features
        
        logger.info(f"Input: {len(feature_files)} files, {total_size:,} bytes, ~{total_features:,} features")
    
    def _log_processing_statistics(self, output_path: Path) -> None:
        """Log comprehensive processing statistics."""
        stats = self.processing_stats
        
        if stats['start_time'] and stats['end_time']:
            duration = stats['end_time'] - stats['start_time']
            duration_str = str(duration).split('.')[0]  # Remove microseconds
            
            compression_ratio = 0
            if stats['input_size_bytes'] > 0:
                compression_ratio = stats['output_size_bytes'] / stats['input_size_bytes']
            
            logger.info(f"Tile generation completed:")
            logger.info(f"  Duration: {duration_str}")
            logger.info(f"  Input: {stats['input_files']} files, {stats['input_size_bytes']:,} bytes")
            logger.info(f"  Output: {stats['tiles_generated']:,} tiles, {stats['output_size_bytes']:,} bytes")
            logger.info(f"  Compression: {compression_ratio:.2f}x")
            logger.info(f"  Features: {stats['features_processed']:,}")
            logger.info(f"  Peak memory: {stats['memory_peak_mb']:.1f}%")
            if stats['retries'] > 0:
                logger.info(f"  Retries: {stats['retries']}")
    
    def get_tile_info(self, mbtiles_path: Path) -> Dict[str, Any]:
        """
        Get comprehensive information about generated MBTiles file.
        
        Args:
            mbtiles_path: Path to MBTiles file
            
        Returns:
            Dictionary with detailed tile information
        """
        try:
            info = {}
            
            with sqlite3.connect(mbtiles_path) as conn:
                cursor = conn.cursor()
                
                # Get metadata
                cursor.execute("SELECT name, value FROM metadata")
                info['metadata'] = dict(cursor.fetchall())
                
                # Get tile statistics
                cursor.execute("SELECT COUNT(*) FROM tiles")
                info['tile_count'] = cursor.fetchone()[0]
                
                cursor.execute("SELECT MIN(zoom_level), MAX(zoom_level) FROM tiles")
                min_zoom, max_zoom = cursor.fetchone()
                info['zoom_range'] = {'min': min_zoom, 'max': max_zoom}
                
                # Get tiles per zoom level
                cursor.execute("SELECT zoom_level, COUNT(*) FROM tiles GROUP BY zoom_level ORDER BY zoom_level")
                info['tiles_per_zoom'] = dict(cursor.fetchall())
                
                # Get tile size statistics
                cursor.execute("SELECT AVG(LENGTH(tile_data)), MIN(LENGTH(tile_data)), MAX(LENGTH(tile_data)) FROM tiles")
                avg_size, min_size, max_size = cursor.fetchone()
                info['tile_sizes'] = {
                    'average_bytes': int(avg_size) if avg_size else 0,
                    'min_bytes': min_size or 0,
                    'max_bytes': max_size or 0
                }
                
                # File information
                stat = mbtiles_path.stat()
                info['file_info'] = {
                    'size_bytes': stat.st_size,
                    'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                }
                
                # Processing statistics if available
                if hasattr(self, 'processing_stats'):
                    info['processing_stats'] = self.processing_stats.copy()
                    # Convert datetime objects to ISO strings
                    for key, value in info['processing_stats'].items():
                        if isinstance(value, datetime):
                            info['processing_stats'][key] = value.isoformat()
            
            return info
            
        except Exception as e:
            logger.error(f"Error reading MBTiles info: {e}")
            return {'error': str(e)}
    
    def validate_tippecanoe(self) -> bool:
        """
        Check if tippecanoe is available and get version info.
        
        Returns:
            True if tippecanoe is available and functional
        """
        try:
            self._validate_tippecanoe()
            return True
        except TippecanoeError:
            return False
    
    def cleanup_temp_files(self) -> None:
        """Clean up temporary files and directories."""
        try:
            if self.temp_dir.exists():
                for item in self.temp_dir.iterdir():
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)
                logger.debug(f"Cleaned up temporary directory: {self.temp_dir}")
        except Exception as e:
            logger.warning(f"Failed to cleanup temporary files: {e}")
    
    def get_processing_info(self) -> Dict[str, Any]:
        """
        Get information about tile generation capabilities and settings.
        
        Returns:
            Dictionary with processing information
        """
        return {
            'tippecanoe_available': self.validate_tippecanoe(),
            'config': {
                'zoom_range': f"{self.config.tiles.min_zoom}-{self.config.tiles.max_zoom}",
                'quality_profile': self.config.tiles.quality_profile,
                'buffer': self.config.tiles.buffer,
                'parallel_processing': self.config.tiles.parallel_processing
            },
            'system': {
                'available_memory_gb': psutil.virtual_memory().available // (1024**3),
                'cpu_count': psutil.cpu_count(),
                'temp_dir': str(self.temp_dir)
            },
            'processing_stats': self.processing_stats.copy() if hasattr(self, 'processing_stats') else {}
        } 