"""
OSM data downloader using Overpass API with robust error handling and retry logic.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any
import tempfile
import shutil

import httpx
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

from tilecraft.models.config import BoundingBox, TilecraftConfig
from tilecraft.utils.cache import CacheManager
from tilecraft.core.bbox import bbox_to_overpass_query, validate_bbox

logger = logging.getLogger(__name__)


class OverpassAPIError(Exception):
    """Custom exception for Overpass API errors."""
    pass


class RateLimitError(OverpassAPIError):
    """Exception for rate limit errors."""
    pass


class TimeoutError(OverpassAPIError):
    """Exception for timeout errors."""
    pass


class OSMDownloader:
    """Downloads OSM data from Overpass API with robust error handling."""
    
    # Overpass API endpoints (fallback list)
    OVERPASS_ENDPOINTS = [
        "https://overpass-api.de/api/interpreter",
        "https://lz4.overpass-api.de/api/interpreter",
        "https://z.overpass-api.de/api/interpreter",
    ]
    
    # Rate limiting and retry configuration
    MAX_RETRIES = 5
    BASE_RETRY_DELAY = 2.0  # seconds
    MAX_RETRY_DELAY = 60.0  # seconds
    REQUEST_TIMEOUT = 600.0  # 10 minutes
    RATE_LIMIT_DELAY = 30.0  # seconds to wait on rate limit
    
    def __init__(self, config: TilecraftConfig, cache_manager: CacheManager):
        """
        Initialize OSM downloader.
        
        Args:
            config: Tilecraft configuration
            cache_manager: Cache manager instance
        """
        self.config = config
        self.cache_manager = cache_manager
        self.current_endpoint_index = 0
        self.last_request_time = 0.0
        self.min_request_interval = 1.0  # Minimum seconds between requests
        
        # Create temp directory for downloads
        self.temp_dir = Path(tempfile.gettempdir()) / "tilecraft"
        self.temp_dir.mkdir(exist_ok=True)
        
    @property
    def current_endpoint(self) -> str:
        """Get current Overpass API endpoint."""
        return self.OVERPASS_ENDPOINTS[self.current_endpoint_index]
    
    def _rotate_endpoint(self) -> None:
        """Rotate to next Overpass API endpoint."""
        self.current_endpoint_index = (self.current_endpoint_index + 1) % len(self.OVERPASS_ENDPOINTS)
        logger.info(f"Rotating to endpoint: {self.current_endpoint}")
    
    def _respect_rate_limit(self) -> None:
        """Ensure minimum interval between requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            sleep_time = self.min_request_interval - elapsed
            logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def _calculate_retry_delay(self, attempt: int, base_delay: float = None) -> float:
        """
        Calculate exponential backoff delay with jitter.
        
        Args:
            attempt: Retry attempt number (0-based)
            base_delay: Base delay in seconds
            
        Returns:
            Delay in seconds
        """
        if base_delay is None:
            base_delay = self.BASE_RETRY_DELAY
            
        # Exponential backoff with jitter
        delay = min(base_delay * (2 ** attempt), self.MAX_RETRY_DELAY)
        # Add random jitter (±25%) but ensure we don't exceed MAX_RETRY_DELAY
        import random
        jitter = delay * 0.25 * (random.random() - 0.5)
        final_delay = delay + jitter
        return max(1.0, min(final_delay, self.MAX_RETRY_DELAY))
    
    def _parse_overpass_error(self, response_text: str) -> str:
        """
        Parse Overpass API error message.
        
        Args:
            response_text: Response text from API
            
        Returns:
            Parsed error message
        """
        if "rate_limited" in response_text.lower():
            return "Rate limited by Overpass API"
        elif "timeout" in response_text.lower():
            return "Query timeout on Overpass API"
        elif "too many requests" in response_text.lower():
            return "Too many requests to Overpass API"
        elif "runtime error" in response_text.lower():
            return "Runtime error on Overpass API"
        else:
            # Extract first line of error for brevity
            first_line = response_text.split('\n')[0]
            return f"Overpass API error: {first_line[:200]}"
    
    async def _download_with_progress(
        self, 
        query: str, 
        output_path: Path,
        progress: Progress,
        task_id: int
    ) -> None:
        """
        Download OSM data with progress tracking.
        
        Args:
            query: Overpass QL query
            output_path: Path to save downloaded data
            progress: Rich progress instance
            task_id: Progress task ID
        """
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Tilecraft OSM Downloader/1.0'
        }
        
        timeout = httpx.Timeout(self.REQUEST_TIMEOUT)
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                progress.update(task_id, description="Sending request...")
                
                async with client.stream(
                    'POST',
                    self.current_endpoint,
                    data=query,
                    headers=headers
                ) as response:
                    
                    # Check for HTTP errors
                    if response.status_code != 200:
                        error_text = await response.atext()
                        error_msg = self._parse_overpass_error(error_text)
                        
                        if response.status_code == 429:
                            raise RateLimitError(f"Rate limited: {error_msg}")
                        elif response.status_code >= 500:
                            raise OverpassAPIError(f"Server error ({response.status_code}): {error_msg}")
                        else:
                            raise OverpassAPIError(f"HTTP {response.status_code}: {error_msg}")
                    
                    # Get content length for progress tracking
                    content_length = response.headers.get('content-length')
                    total_size = int(content_length) if content_length else None
                    
                    if total_size:
                        progress.update(task_id, total=total_size, description="Downloading...")
                    else:
                        progress.update(task_id, description="Downloading (unknown size)...")
                    
                    # Download with progress tracking
                    downloaded = 0
                    with open(output_path, 'wb') as f:
                        async for chunk in response.aiter_bytes(chunk_size=8192):
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                            if total_size:
                                progress.update(task_id, completed=downloaded)
                    
                    progress.update(task_id, description="Download complete")
                    
            except httpx.TimeoutException:
                raise TimeoutError(f"Request timeout after {self.REQUEST_TIMEOUT}s")
            except httpx.NetworkError as e:
                raise OverpassAPIError(f"Network error: {e}")
    
    def download(self, bbox: BoundingBox) -> Path:
        """
        Download OSM data for bounding box with comprehensive error handling.
        
        Args:
            bbox: Bounding box to download
            
        Returns:
            Path to downloaded OSM data file
            
        Raises:
            ValueError: Invalid bounding box
            OverpassAPIError: API-related errors
            RuntimeError: Other download failures
        """
        # Validate bounding box
        if not validate_bbox(bbox):
            raise ValueError(f"Invalid bounding box: {bbox.to_string()}")
        
        bbox_str = bbox.to_string()
        
        # Check cache first
        cached_path = self.cache_manager.get_cached_osm_data(bbox_str)
        if cached_path and cached_path.exists():
            file_size = cached_path.stat().st_size
            logger.info(f"Using cached OSM data: {cached_path} ({file_size:,} bytes)")
            return cached_path
        
        logger.info(f"Downloading OSM data for bbox: {bbox_str} (area: {bbox.area_degrees:.4f}°²)")
        
        # Generate Overpass query
        feature_types = [f.value for f in self.config.features.types]
        query = bbox_to_overpass_query(bbox, feature_types)
        
        # Log query for debugging
        if self.config.verbose:
            logger.debug(f"Overpass query:\n{query}")
        
        # Download with retry logic
        output_path = self._download_with_retry(query, bbox_str)
        
        # Validate downloaded file
        if not output_path.exists() or output_path.stat().st_size == 0:
            raise RuntimeError("Downloaded file is empty or missing")
        
        # Cache the result
        try:
            cached_path = self.cache_manager.cache_osm_data(bbox_str, output_path)
            logger.info(f"Downloaded and cached OSM data: {cached_path} ({cached_path.stat().st_size:,} bytes)")
            return cached_path
        except Exception as e:
            logger.warning(f"Failed to cache OSM data: {e}")
            return output_path
    
    def _download_with_retry(self, query: str, bbox_str: str) -> Path:
        """
        Download OSM data with retry logic and endpoint rotation.
        
        Args:
            query: Overpass QL query
            bbox_str: Bounding box string for filename
            
        Returns:
            Path to downloaded file
        """
        output_path = self.temp_dir / f"osm_data_{bbox_str.replace(',', '_')}.osm"
        last_exception = None
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=None if self.config.verbose else None
        ) as progress:
            
            task_id = progress.add_task("Preparing download...", total=None)
            
            for attempt in range(self.MAX_RETRIES):
                try:
                    # Respect rate limiting
                    self._respect_rate_limit()
                    
                    progress.update(
                        task_id, 
                        description=f"Attempt {attempt + 1}/{self.MAX_RETRIES} ({self.current_endpoint})"
                    )
                    
                    # Perform download
                    asyncio.run(self._download_with_progress(query, output_path, progress, task_id))
                    
                    # Success!
                    return output_path
                    
                except RateLimitError as e:
                    last_exception = e
                    logger.warning(f"Rate limited on attempt {attempt + 1}: {e}")
                    
                    if attempt < self.MAX_RETRIES - 1:
                        # Wait longer for rate limits
                        delay = self.RATE_LIMIT_DELAY + (attempt * 15)
                        progress.update(task_id, description=f"Rate limited, waiting {delay}s...")
                        time.sleep(delay)
                        
                        # Try different endpoint
                        self._rotate_endpoint()
                    
                except TimeoutError as e:
                    last_exception = e
                    logger.warning(f"Timeout on attempt {attempt + 1}: {e}")
                    
                    if attempt < self.MAX_RETRIES - 1:
                        delay = self._calculate_retry_delay(attempt)
                        progress.update(task_id, description=f"Timeout, retrying in {delay:.1f}s...")
                        time.sleep(delay)
                        
                        # Try different endpoint on timeout
                        self._rotate_endpoint()
                
                except OverpassAPIError as e:
                    last_exception = e
                    logger.warning(f"API error on attempt {attempt + 1}: {e}")
                    
                    if attempt < self.MAX_RETRIES - 1:
                        delay = self._calculate_retry_delay(attempt)
                        progress.update(task_id, description=f"API error, retrying in {delay:.1f}s...")
                        time.sleep(delay)
                        
                        # Rotate endpoint on persistent errors
                        if attempt >= 1:
                            self._rotate_endpoint()
                
                except Exception as e:
                    last_exception = e
                    logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
                    
                    if attempt < self.MAX_RETRIES - 1:
                        delay = self._calculate_retry_delay(attempt, base_delay=5.0)
                        progress.update(task_id, description=f"Error, retrying in {delay:.1f}s...")
                        time.sleep(delay)
            
            # All retries exhausted
            progress.update(task_id, description="Download failed")
            
        # Clean up partial download
        if output_path.exists():
            try:
                output_path.unlink()
            except Exception:
                pass
        
        # Raise the last exception
        if isinstance(last_exception, (RateLimitError, TimeoutError, OverpassAPIError)):
            raise last_exception
        else:
            raise RuntimeError(f"OSM download failed after {self.MAX_RETRIES} attempts: {last_exception}")
    
    def get_download_info(self, bbox: BoundingBox) -> Dict[str, Any]:
        """
        Get information about what would be downloaded without actually downloading.
        
        Args:
            bbox: Bounding box to analyze
            
        Returns:
            Dictionary with download information
        """
        bbox_str = bbox.to_string()
        feature_types = [f.value for f in self.config.features.types]
        query = bbox_to_overpass_query(bbox, feature_types)
        
        return {
            "bbox": bbox_str,
            "area_degrees": bbox.area_degrees,
            "feature_types": feature_types,
            "query_length": len(query),
            "cached": self.cache_manager.get_cached_osm_data(bbox_str) is not None,
            "endpoints": self.OVERPASS_ENDPOINTS,
            "current_endpoint": self.current_endpoint,
            "temp_dir": str(self.temp_dir),
        }
    
    def download_geofabrik(self, bbox: BoundingBox) -> Optional[Path]:
        """
        Download from Geofabrik (future implementation).
        
        Args:
            bbox: Bounding box
            
        Returns:
            Path to downloaded file or None
        """
        # TODO: Implement Geofabrik download as fallback
        logger.warning("Geofabrik download not yet implemented")
        return None
    
    def cleanup_temp_files(self) -> None:
        """Clean up temporary download files."""
        try:
            if self.temp_dir.exists():
                for file_path in self.temp_dir.glob("osm_data_*.osm"):
                    if file_path.is_file():
                        file_path.unlink()
                        logger.debug(f"Cleaned up temp file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup temp files: {e}") 