"""
Cache management utilities.
"""

import hashlib
import json
import logging
from pathlib import Path
from typing import Optional, Union

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages caching of OSM data and intermediate processing results."""

    def __init__(self, cache_dir: Path, enabled: bool = True):
        """
        Initialize cache manager.

        Args:
            cache_dir: Directory for cache storage
            enabled: Whether caching is enabled
        """
        self.cache_dir = Path(cache_dir)
        self.enabled = enabled

        if self.enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Cache initialized: {self.cache_dir}")

    def _get_cache_key(self, data: Union[str, dict]) -> str:
        """
        Generate cache key from data.

        Args:
            data: Data to generate key from

        Returns:
            MD5 hash as hex string
        """
        if isinstance(data, str):
            content = data
        else:
            content = json.dumps(data, sort_keys=True)

        return hashlib.md5(content.encode()).hexdigest()

    def get_path(self, key: str, suffix: str = "") -> Path:
        """
        Get cache file path for key.

        Args:
            key: Cache key
            suffix: File suffix/extension

        Returns:
            Path to cache file
        """
        filename = f"{key}{suffix}"
        return self.cache_dir / filename

    def exists(self, key: str, suffix: str = "") -> bool:
        """
        Check if cache entry exists.

        Args:
            key: Cache key
            suffix: File suffix/extension

        Returns:
            True if cache entry exists
        """
        if not self.enabled:
            return False

        cache_path = self.get_path(key, suffix)
        return cache_path.exists()

    def get(self, key: str, suffix: str = "") -> Optional[Path]:
        """
        Get cached file path if it exists.

        Args:
            key: Cache key
            suffix: File suffix/extension

        Returns:
            Path to cached file or None if not found
        """
        if not self.enabled:
            return None

        cache_path = self.get_path(key, suffix)
        if cache_path.exists():
            logger.debug(f"Cache hit: {cache_path}")
            return cache_path

        logger.debug(f"Cache miss: {key}")
        return None

    def put(self, key: str, source_path: Path, suffix: str = "") -> Path:
        """
        Store file in cache.

        Args:
            key: Cache key
            source_path: Path to source file
            suffix: File suffix/extension

        Returns:
            Path to cached file
        """
        if not self.enabled:
            return source_path

        cache_path = self.get_path(key, suffix)

        # Copy or move file to cache
        if source_path != cache_path:
            try:
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                import shutil
                import os

                # Check if source file exists and is readable
                if not source_path.exists():
                    raise FileNotFoundError(f"Source file not found: {source_path}")
                
                if not os.access(source_path, os.R_OK):
                    raise PermissionError(f"Cannot read source file: {source_path}")

                # Check available disk space (estimate 2x source file size needed)
                source_size = source_path.stat().st_size
                available_space = shutil.disk_usage(cache_path.parent).free
                
                if available_space < source_size * 2:
                    raise OSError(
                        f"Insufficient disk space. Available: {available_space // 1024 // 1024}MB, "
                        f"Required: {source_size * 2 // 1024 // 1024}MB"
                    )

                # Check write permissions on cache directory
                if not os.access(cache_path.parent, os.W_OK):
                    raise PermissionError(f"Cannot write to cache directory: {cache_path.parent}")

                # Perform atomic copy operation
                temp_cache_path = cache_path.with_suffix(cache_path.suffix + ".tmp")
                try:
                    shutil.copy2(source_path, temp_cache_path)
                    temp_cache_path.rename(cache_path)
                    logger.debug(f"Cached: {cache_path}")
                except Exception:
                    # Cleanup temporary file on failure
                    if temp_cache_path.exists():
                        try:
                            temp_cache_path.unlink()
                        except Exception:
                            pass
                    raise
                    
            except (OSError, PermissionError, FileNotFoundError) as e:
                logger.error(f"Failed to cache file {source_path}: {e}")
                # Return source path if caching fails - allow operation to continue
                return source_path
            except Exception as e:
                logger.error(f"Unexpected error caching file {source_path}: {e}")
                return source_path

        return cache_path

    def cache_osm_data(self, bbox_str: str, data_path: Path) -> Path:
        """
        Cache OSM data file.

        Args:
            bbox_str: Bounding box string
            data_path: Path to OSM data file

        Returns:
            Path to cached file
        """
        key = self._get_cache_key(f"osm_data_{bbox_str}")
        return self.put(key, data_path, ".osm")

    def get_cached_osm_data(self, bbox_str: str) -> Optional[Path]:
        """
        Get cached OSM data if available.

        Args:
            bbox_str: Bounding box string

        Returns:
            Path to cached file or None
        """
        key = self._get_cache_key(f"osm_data_{bbox_str}")
        return self.get(key, ".osm")

    def cache_features(
        self, feature_type: str, bbox_str: str, geojson_path: Path
    ) -> Path:
        """
        Cache extracted feature GeoJSON.

        Args:
            feature_type: Type of feature
            bbox_str: Bounding box string
            geojson_path: Path to GeoJSON file

        Returns:
            Path to cached file
        """
        key = self._get_cache_key(f"features_{feature_type}_{bbox_str}")
        return self.put(key, geojson_path, ".geojson")

    def get_cached_features(self, feature_type: str, bbox_str: str) -> Optional[Path]:
        """
        Get cached feature GeoJSON if available.

        Args:
            feature_type: Type of feature
            bbox_str: Bounding box string

        Returns:
            Path to cached file or None
        """
        key = self._get_cache_key(f"features_{feature_type}_{bbox_str}")
        return self.get(key, ".geojson")

    def cache_tiles(self, cache_key: str, mbtiles_path: Path) -> Path:
        """
        Cache generated MBTiles file.

        Args:
            cache_key: Cache key for tiles
            mbtiles_path: Path to MBTiles file

        Returns:
            Path to cached file
        """
        return self.put(cache_key, mbtiles_path, ".mbtiles")

    def get_cached_tiles(self, cache_key: str) -> Optional[Path]:
        """
        Get cached MBTiles file if available.

        Args:
            cache_key: Cache key for tiles

        Returns:
            Path to cached file or None
        """
        return self.get(cache_key, ".mbtiles")

    def clear(self) -> None:
        """Clear all cache files."""
        if not self.enabled or not self.cache_dir.exists():
            return

        import shutil

        shutil.rmtree(self.cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Cache cleared")

    def get_size(self) -> int:
        """
        Get total cache size in bytes.

        Returns:
            Total size of cached files in bytes
        """
        if not self.enabled or not self.cache_dir.exists():
            return 0

        total_size = 0
        for file_path in self.cache_dir.rglob("*"):
            try:
                if file_path.is_file():
                    # Use lstat to avoid following symlinks and handle race conditions
                    stat_info = file_path.lstat()
                    if stat_info.st_nlink > 0:  # File still exists
                        total_size += stat_info.st_size
            except (OSError, FileNotFoundError):
                # File may have been deleted between iteration and stat call
                # Skip and continue with next file
                continue
            except Exception as e:
                logger.warning(f"Error getting size of {file_path}: {e}")
                continue

        return total_size
