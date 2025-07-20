"""
Feature extraction from OSM data using osmium with robust error handling and performance optimization.
"""

import json
import logging
import tempfile
import time
from pathlib import Path
from typing import Any, Optional

import osmium
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)

from tilecraft.models.config import FeatureType, TilecraftConfig
from tilecraft.utils.cache import CacheManager

logger = logging.getLogger(__name__)


class FeatureExtractionError(Exception):
    """Custom exception for feature extraction errors."""

    pass


class OSMProcessingError(FeatureExtractionError):
    """Exception for OSM processing errors."""

    pass


class GeometryValidationError(FeatureExtractionError):
    """Exception for geometry validation errors."""

    pass


class OSMFeatureHandler(osmium.SimpleHandler):
    """Osmium handler for extracting specific features from OSM data."""

    def __init__(self, feature_type: FeatureType, tag_filters: dict[str, list[str]]):
        """
        Initialize feature handler.

        Args:
            feature_type: Type of feature to extract
            tag_filters: Dictionary of tag filters to apply
        """
        super().__init__()
        self.feature_type = feature_type
        self.tag_filters = tag_filters
        self.features = []
        self.processed_count = 0
        self.error_count = 0

        # Debug counters
        self.nodes_seen = 0
        self.ways_seen = 0
        self.ways_matched = 0

        # Debug logging
        logger.debug(
            f"OSMFeatureHandler initialized for {feature_type.value} with filters: {tag_filters}"
        )

    def node(self, n):
        """Process OSM nodes."""
        self.nodes_seen += 1

        if self._matches_filters(n.tags):
            try:
                feature = self._create_point_feature(n)
                if feature:
                    self.features.append(feature)
                    self.processed_count += 1
            except Exception as e:
                self.error_count += 1
                logger.debug(f"Error processing node {n.id}: {e}")

    def way(self, w):
        """Process OSM ways."""
        self.ways_seen += 1

        if self.ways_seen <= 3:
            logger.info(f"Processing way {w.id} with tags: {dict(w.tags)}")

        if self._matches_filters(w.tags):
            self.ways_matched += 1
            logger.info(f"Way {w.id} MATCHED! Creating feature...")
            try:
                feature = self._create_way_feature(w)
                if feature:
                    self.features.append(feature)
                    self.processed_count += 1
                    logger.info(f"Way {w.id} feature created successfully")
                else:
                    logger.warning(f"Way {w.id} matched but feature creation failed")
            except Exception as e:
                self.error_count += 1
                logger.error(f"Error processing way {w.id}: {e}")

    def relation(self, r):
        """Process OSM relations."""
        if self._matches_filters(r.tags):
            try:
                # For now, we'll skip relations as they require more complex processing
                # TODO: Implement multipolygon relation processing
                self.processed_count += 1
            except Exception as e:
                self.error_count += 1
                logger.debug(f"Error processing relation {r.id}: {e}")

    def _matches_filters(self, tags) -> bool:
        """
        Check if OSM element tags match the filters.

        Args:
            tags: OSM element tags

        Returns:
            True if tags match filters
        """
        # Reduced debug logging
        should_debug = False  # Turn off excessive debug logging

        if should_debug:
            logger.debug(
                f"Checking tags: {dict(tags)} against filters: {self.tag_filters}"
            )

        for key, values in self.tag_filters.items():
            if key in tags:
                tag_value = tags[key]
                # Handle wildcard matches
                if "*" in values:
                    if should_debug:
                        logger.debug(f"Wildcard match found: {key}={tag_value}")
                    return True
                # Handle exact matches
                if tag_value in values:
                    if should_debug:
                        logger.debug(f"Exact match found: {key}={tag_value}")
                    return True
                # Handle pattern matches (basic support)
                for value in values:
                    if "~" in value:
                        # Simple regex-like matching
                        pattern = value.replace("~", "")
                        if pattern in tag_value:
                            if should_debug:
                                logger.debug(
                                    f"Pattern match found: {key}={tag_value} matches {pattern}"
                                )
                            return True

        if should_debug:
            logger.debug(f"No match found for tags: {dict(tags)}")
        return False

    def _create_point_feature(self, node) -> Optional[dict[str, Any]]:
        """
        Create GeoJSON feature from OSM node.

        Args:
            node: OSM node

        Returns:
            GeoJSON feature or None
        """
        if not node.location.valid():
            return None

        properties = dict(node.tags)
        properties["osm_id"] = node.id
        properties["osm_type"] = "node"

        return {
            "type": "Feature",
            "properties": properties,
            "geometry": {
                "type": "Point",
                "coordinates": [float(node.location.lon), float(node.location.lat)],
            },
        }

    def _create_way_feature(self, way) -> Optional[dict[str, Any]]:
        """
        Create GeoJSON feature from OSM way.

        Args:
            way: OSM way

        Returns:
            GeoJSON feature or None
        """
        if len(way.nodes) < 2:
            logger.debug(f"Way {way.id}: Not enough nodes ({len(way.nodes)})")
            return None

        # Extract coordinates
        coordinates = []
        for node in way.nodes:
            if node.location.valid():
                coordinates.append([float(node.location.lon), float(node.location.lat)])

        if len(coordinates) < 2:
            logger.debug(
                f"Way {way.id}: Not enough valid coordinates ({len(coordinates)} from {len(way.nodes)} nodes)"
            )
            return None

        properties = dict(way.tags)
        properties["osm_id"] = way.id
        properties["osm_type"] = "way"

        # Determine geometry type
        is_closed = len(coordinates) > 2 and coordinates[0] == coordinates[-1]

        # Decide between LineString and Polygon based on tags and closure
        geometry_type = self._determine_geometry_type(way.tags, is_closed)

        if geometry_type == "Polygon":
            # Ensure polygon is closed
            if len(coordinates) > 2 and coordinates[0] != coordinates[-1]:
                coordinates.append(coordinates[0])
            geometry = {"type": "Polygon", "coordinates": [coordinates]}
        else:
            geometry = {"type": "LineString", "coordinates": coordinates}

        logger.debug(
            f"Way {way.id}: Created {geometry_type} feature with {len(coordinates)} coordinates"
        )

        return {"type": "Feature", "properties": properties, "geometry": geometry}

    def _determine_geometry_type(self, tags, is_closed: bool) -> str:
        """
        Determine appropriate geometry type based on tags and shape.

        Args:
            tags: OSM element tags (TagList or dict)
            is_closed: Whether the way is closed

        Returns:
            Geometry type string
        """
        # Convert TagList to dict for easier processing
        if hasattr(tags, "keys"):
            # It's already a dict-like object
            tags_dict = dict(tags)
        else:
            # Convert TagList to dict
            tags_dict = dict(tags)

        # Area tags that suggest polygon geometry
        area_tags = {
            "building",
            "landuse",
            "natural",
            "leisure",
            "amenity",
            "place",
            "tourism",
            "shop",
            "area",
        }

        # Line tags that suggest linestring geometry
        line_tags = {"highway", "waterway", "railway", "barrier", "power"}

        # Check for explicit area tag
        if tags_dict.get("area") == "yes":
            return "Polygon"
        if tags_dict.get("area") == "no":
            return "LineString"

        # Check tag implications
        for tag_key in tags_dict.keys():
            if tag_key in area_tags and is_closed:
                return "Polygon"
            if tag_key in line_tags:
                return "LineString"

        # Default logic
        if is_closed and len(set(tags_dict.keys()) & area_tags) > 0:
            return "Polygon"

        return "LineString"


class FeatureExtractor:
    """Extracts specific features from OSM data with robust error handling."""

    # Processing configuration
    MAX_RETRIES = 3
    CHUNK_SIZE = 10000  # Features to process before yielding
    MEMORY_LIMIT_MB = 500  # Memory limit for processing

    def __init__(self, config: TilecraftConfig, cache_manager: CacheManager):
        """
        Initialize feature extractor.

        Args:
            config: Tilecraft configuration
            cache_manager: Cache manager instance
        """
        self.config = config
        self.cache_manager = cache_manager
        self.output_dir = config.output.data_dir

        # Create temp directory for processing
        self.temp_dir = Path(tempfile.gettempdir()) / "tilecraft" / "extraction"
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        # Enhanced feature type to OSM tag mappings
        self.feature_mappings = {
            # Water Features
            FeatureType.RIVERS: {
                "waterway": ["river", "stream", "canal", "drain", "ditch", "waterfall"]
            },
            FeatureType.WATER: {
                "natural": ["water", "bay", "strait"],
                "landuse": ["reservoir", "basin"],
            },
            FeatureType.LAKES: {
                "natural": ["water"],
                "landuse": ["reservoir", "basin"],
            },
            FeatureType.WETLANDS: {"natural": ["wetland", "marsh", "swamp"]},
            FeatureType.WATERWAYS: {
                "waterway": ["river", "stream", "canal", "drain", "ditch", "rapids", "waterfall"]
            },
            FeatureType.COASTLINE: {"natural": ["coastline", "beach", "bay"]},
            
            # Natural Features
            FeatureType.FOREST: {
                "natural": ["wood", "forest", "scrub"],
                "landuse": ["forest", "forestry"],
            },
            FeatureType.WOODS: {"natural": ["wood", "forest"]},
            FeatureType.MOUNTAINS: {"natural": ["peak", "ridge", "saddle", "volcano"]},
            FeatureType.PEAKS: {"natural": ["peak", "volcano"]},
            FeatureType.CLIFFS: {"natural": ["cliff", "rock", "scree", "stone"]},
            FeatureType.BEACHES: {"natural": ["beach", "sand", "shingle"]},
            FeatureType.GLACIERS: {"natural": ["glacier"]},
            FeatureType.VOLCANOES: {"natural": ["volcano"]},
            
            # Land Use
            FeatureType.PARKS: {
                "leisure": ["park", "nature_reserve", "recreation_ground", "garden"],
                "boundary": ["national_park", "protected_area"],
            },
            FeatureType.FARMLAND: {
                "landuse": ["farmland", "orchard", "vineyard", "plant_nursery", "greenhouse_horticulture"]
            },
            FeatureType.RESIDENTIAL: {"landuse": ["residential"]},
            FeatureType.COMMERCIAL: {"landuse": ["commercial", "retail"]},
            FeatureType.INDUSTRIAL: {"landuse": ["industrial", "port", "quarry"]},
            FeatureType.MILITARY: {"landuse": ["military"], "military": ["*"]},
            FeatureType.CEMETERIES: {"landuse": ["cemetery"], "amenity": ["grave_yard"]},
            
            # Transportation
            FeatureType.ROADS: {
                "highway": [
                    "motorway", "trunk", "primary", "secondary", "tertiary",
                    "unclassified", "residential", "service", "track",
                ]
            },
            FeatureType.HIGHWAYS: {
                "highway": ["motorway", "motorway_link", "trunk", "trunk_link"]
            },
            FeatureType.RAILWAYS: {
                "railway": ["rail", "tram", "light_rail", "subway", "monorail", "narrow_gauge", "abandoned"]
            },
            FeatureType.AIRPORTS: {
                "aeroway": ["aerodrome", "runway", "taxiway", "terminal", "gate", "apron"]
            },
            FeatureType.BRIDGES: {"bridge": ["yes"], "man_made": ["bridge"]},
            FeatureType.TUNNELS: {"tunnel": ["yes"], "man_made": ["tunnel"]},
            FeatureType.PATHS: {
                "highway": ["path", "footway", "cycleway", "bridleway", "steps"]
            },
            FeatureType.CYCLEWAYS: {"highway": ["cycleway"], "cycleway": ["*"]},
            
            # Built Environment
            FeatureType.BUILDINGS: {"building": ["*"]},
            FeatureType.CHURCHES: {
                "building": ["church", "cathedral", "chapel"],
                "amenity": ["place_of_worship"]
            },
            FeatureType.SCHOOLS: {
                "building": ["school"],
                "amenity": ["school", "kindergarten", "university", "college"]
            },
            FeatureType.HOSPITALS: {
                "building": ["hospital"],
                "amenity": ["hospital", "clinic", "doctors"]
            },
            FeatureType.UNIVERSITIES: {
                "building": ["university", "college"],
                "amenity": ["university", "college"]
            },
            
            # Amenities
            FeatureType.RESTAURANTS: {
                "amenity": ["restaurant", "fast_food", "cafe", "bar", "pub", "food_court"]
            },
            FeatureType.SHOPS: {
                "shop": ["*"],
                "building": ["retail", "shop"],
                "amenity": ["marketplace"]
            },
            FeatureType.HOTELS: {
                "tourism": ["hotel", "motel", "hostel", "guest_house"],
                "building": ["hotel"]
            },
            FeatureType.BANKS: {"amenity": ["bank", "atm"], "building": ["bank"]},
            FeatureType.FUEL_STATIONS: {"amenity": ["fuel"], "building": ["fuel"]},
            FeatureType.POST_OFFICES: {"amenity": ["post_office"], "building": ["post_office"]},
            
            # Recreation
            FeatureType.PLAYGROUNDS: {"leisure": ["playground"]},
            FeatureType.SPORTS_FIELDS: {
                "leisure": ["sports_centre", "stadium", "pitch"],
                "sport": ["*"]
            },
            FeatureType.GOLF_COURSES: {"leisure": ["golf_course"], "sport": ["golf"]},
            FeatureType.STADIUMS: {"leisure": ["stadium"], "building": ["stadium"]},
            FeatureType.SWIMMING_POOLS: {
                "leisure": ["swimming_pool"],
                "amenity": ["swimming_pool"]
            },
            
            # Infrastructure
            FeatureType.POWER_LINES: {
                "power": ["line", "cable", "transmission", "substation", "tower"],
                "man_made": ["transmission_line"]
            },
            FeatureType.WIND_TURBINES: {
                "generator:source": ["wind"],
                "man_made": ["wind_turbine"]
            },
            FeatureType.SOLAR_FARMS: {
                "generator:source": ["solar"],
                "landuse": ["industrial"],
                "man_made": ["solar_panel"]
            },
            FeatureType.DAMS: {"waterway": ["dam"], "man_made": ["dam"]},
            FeatureType.BARRIERS: {
                "barrier": ["wall", "fence", "hedge", "retaining_wall", "city_wall"]
            },
            
            # Administrative
            FeatureType.BOUNDARIES: {
                "boundary": ["administrative", "political", "postal_code"],
                "admin_level": ["*"],
                "place": ["state", "county", "city", "town", "village"],
                "tiger:cfcc": ["*"],  # US Census boundaries
            },
            FeatureType.PROTECTED_AREAS: {
                "boundary": ["protected_area", "national_park"],
                "leisure": ["nature_reserve"]
            },
        }

    def extract(
        self, osm_data_path: Path, feature_types: list[FeatureType]
    ) -> dict[str, Path]:
        """
        Extract features from OSM data with comprehensive error handling.

        Args:
            osm_data_path: Path to OSM data file
            feature_types: List of feature types to extract

        Returns:
            Dictionary mapping feature type to GeoJSON file path

        Raises:
            FeatureExtractionError: Feature extraction failures
            OSMProcessingError: OSM data processing issues
            FileNotFoundError: Missing input files
        """
        if not osm_data_path.exists():
            raise FileNotFoundError(f"OSM data file not found: {osm_data_path}")

        # Validate OSM file
        self._validate_osm_file(osm_data_path)

        logger.info(
            f"Extracting {len(feature_types)} feature types from: {osm_data_path}"
        )
        logger.info(f"File size: {osm_data_path.stat().st_size:,} bytes")

        results = {}

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=None if not self.config.verbose else None,
        ) as progress:

            main_task = progress.add_task(
                f"Processing {len(feature_types)} feature types...",
                total=len(feature_types),
            )

            for i, feature_type in enumerate(feature_types):
                progress.update(
                    main_task, description=f"Extracting {feature_type.value}..."
                )

                try:
                    # Check cache first
                    bbox_str = self.config.bbox.to_string()
                    cached_path = self.cache_manager.get_cached_features(
                        feature_type.value, bbox_str
                    )

                    if cached_path and cached_path.exists():
                        feature_count = self._count_features(cached_path)
                        logger.info(
                            f"Using cached {feature_type.value}: {cached_path} ({feature_count} features)"
                        )
                        results[feature_type.value] = cached_path
                    else:
                        # Extract features
                        output_path = self._extract_feature_type_with_retry(
                            osm_data_path, feature_type, progress
                        )

                        # Cache the result
                        try:
                            cached_path = self.cache_manager.cache_features(
                                feature_type.value, bbox_str, output_path
                            )
                            results[feature_type.value] = cached_path

                            # Log extraction statistics
                            feature_count = self._count_features(cached_path)
                            file_size = cached_path.stat().st_size
                            logger.info(
                                f"Extracted {feature_count} {feature_type.value} features ({file_size:,} bytes)"
                            )

                        except Exception as e:
                            logger.warning(f"Failed to cache {feature_type.value}: {e}")
                            results[feature_type.value] = output_path

                except Exception as e:
                    logger.error(f"Failed to extract {feature_type.value}: {e}")
                    raise FeatureExtractionError(
                        f"Feature extraction failed for {feature_type.value}: {e}"
                    )

                progress.update(main_task, completed=i + 1)

            progress.update(main_task, description="Feature extraction complete")

        return results

    def _validate_osm_file(self, osm_data_path: Path) -> None:
        """
        Validate OSM data file format and contents.

        Args:
            osm_data_path: Path to OSM file

        Raises:
            OSMProcessingError: Invalid OSM file
        """
        try:
            # Check file size
            file_size = osm_data_path.stat().st_size
            if file_size == 0:
                raise OSMProcessingError(f"OSM file is empty: {osm_data_path}")

            # Try to read file header
            if osm_data_path.suffix.lower() in [".osm", ".xml"]:
                with open(osm_data_path, encoding="utf-8") as f:
                    header = f.read(1000)
                    if "<?xml" not in header or "<osm" not in header:
                        raise OSMProcessingError(
                            f"Invalid OSM XML format: {osm_data_path}"
                        )

            elif osm_data_path.suffix.lower() in [".pbf", ".osm"]:
                # For PBF/OSM files, check basic file signature
                try:
                    with open(osm_data_path, "rb") as f:
                        # Check for PBF header (first few bytes should be readable)
                        header = f.read(16)
                        if len(header) < 4:
                            raise OSMProcessingError(
                                "File too small to be a valid PBF file"
                            )
                        # Basic validation - PBF files have specific byte patterns
                        if not header:
                            raise OSMProcessingError("Empty PBF file")
                except OSError as e:
                    raise OSMProcessingError(f"Cannot read PBF file: {e}")

            else:
                logger.warning(f"Unknown OSM file format: {osm_data_path.suffix}")

        except OSMProcessingError:
            raise
        except Exception as e:
            raise OSMProcessingError(f"Failed to validate OSM file: {e}")

    def _extract_feature_type_with_retry(
        self, osm_data_path: Path, feature_type: FeatureType, progress: Progress
    ) -> Path:
        """
        Extract feature type with retry logic.

        Args:
            osm_data_path: Input OSM data file
            feature_type: Feature type to extract
            progress: Progress tracker

        Returns:
            Path to output GeoJSON file
        """
        output_path = self.output_dir / f"{feature_type.value}.geojson"
        last_exception = None

        for attempt in range(self.MAX_RETRIES):
            try:
                task_id = progress.add_task(
                    f"Processing {feature_type.value} (attempt {attempt + 1})...",
                    total=None,
                )

                result_path = self._extract_feature_type(
                    osm_data_path, feature_type, output_path, progress, task_id
                )

                progress.remove_task(task_id)
                return result_path

            except Exception as e:
                last_exception = e
                logger.warning(
                    f"Attempt {attempt + 1} failed for {feature_type.value}: {e}"
                )

                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(2**attempt)  # Exponential backoff

                try:
                    progress.remove_task(task_id)
                except Exception:
                    pass

        raise FeatureExtractionError(
            f"Failed to extract {feature_type.value} after {self.MAX_RETRIES} attempts: {last_exception}"
        )

    def _extract_feature_type(
        self,
        osm_data_path: Path,
        feature_type: FeatureType,
        output_path: Path,
        progress: Progress,
        task_id: int,
    ) -> Path:
        """
        Extract specific feature type using osmium.

        Args:
            osm_data_path: Input OSM data file
            feature_type: Feature type to extract
            output_path: Output GeoJSON file path
            progress: Progress tracker
            task_id: Progress task ID

        Returns:
            Path to output file
        """
        # Create output directory
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Get tag filters for this feature type
        tag_filters = self._get_tag_filters(feature_type)

        # Debug logging
        logger.debug(f"Extracting {feature_type.value} with tag filters: {tag_filters}")

        progress.update(
            task_id, description=f"Processing {feature_type.value} features..."
        )

        try:
            # Create handler for this feature type
            handler = OSMFeatureHandler(feature_type, tag_filters)

            # Process OSM data
            osmium.apply(str(osm_data_path), handler)

            progress.update(
                task_id,
                description=f"Writing {len(handler.features)} {feature_type.value} features...",
            )

            # Create GeoJSON output
            geojson_data = {
                "type": "FeatureCollection",
                "features": handler.features,
                "properties": {
                    "feature_type": feature_type.value,
                    "processed_count": handler.processed_count,
                    "error_count": handler.error_count,
                    "extraction_time": time.time(),
                    "nodes_seen": handler.nodes_seen,
                    "ways_seen": handler.ways_seen,
                    "ways_matched": handler.ways_matched,
                },
            }

            # Write to output file
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(geojson_data, f, indent=2 if self.config.verbose else None)

            # Validate output
            self._validate_geojson_file(output_path)

            progress.update(task_id, description=f"Completed {feature_type.value}")

            if handler.error_count > 0:
                logger.warning(
                    f"Encountered {handler.error_count} errors processing {feature_type.value}"
                )

            return output_path

        except Exception as e:
            # Cleanup partial output
            if output_path.exists():
                try:
                    output_path.unlink()
                except Exception:
                    pass
            raise OSMProcessingError(
                f"OSM processing failed for {feature_type.value}: {e}"
            )

    def _get_tag_filters(self, feature_type: FeatureType) -> dict[str, list[str]]:
        """
        Get OSM tag filters for feature type with custom tag support.

        Args:
            feature_type: Feature type

        Returns:
            Dictionary of tag filters
        """
        base_filters = self.feature_mappings.get(feature_type, {})

        # Add custom tags from configuration
        if (
            self.config.features.custom_tags
            and feature_type.value in self.config.features.custom_tags
        ):

            custom_tags = self.config.features.custom_tags[feature_type.value]
            filters = base_filters.copy()

            # Parse custom tags (format: "key=value" or "key")
            for tag in custom_tags:
                if "=" in tag:
                    key, value = tag.split("=", 1)
                    if key in filters:
                        filters[key].append(value)
                    else:
                        filters[key] = [value]
                else:
                    # Key without value means accept any value
                    filters[tag] = ["*"]

            return filters

        return base_filters

    def _validate_geojson_file(self, geojson_path: Path) -> None:
        """
        Validate GeoJSON file format and geometry.

        Args:
            geojson_path: Path to GeoJSON file

        Raises:
            GeometryValidationError: Invalid GeoJSON
        """
        try:
            with open(geojson_path, encoding="utf-8") as f:
                data = json.load(f)

            # Basic structure validation
            if not isinstance(data, dict):
                raise GeometryValidationError("GeoJSON must be a dictionary")

            if data.get("type") != "FeatureCollection":
                raise GeometryValidationError("GeoJSON must be a FeatureCollection")

            features = data.get("features", [])
            if not isinstance(features, list):
                raise GeometryValidationError("Features must be a list")

            # Validate a sample of features
            sample_size = min(10, len(features))
            for i, feature in enumerate(features[:sample_size]):
                self._validate_feature(feature, i)

        except GeometryValidationError:
            raise
        except Exception as e:
            raise GeometryValidationError(f"Failed to validate GeoJSON: {e}")

    def _validate_feature(self, feature: dict[str, Any], index: int) -> None:
        """
        Validate individual GeoJSON feature.

        Args:
            feature: GeoJSON feature
            index: Feature index for error reporting
        """
        if not isinstance(feature, dict):
            raise GeometryValidationError(f"Feature {index} must be a dictionary")

        if feature.get("type") != "Feature":
            raise GeometryValidationError(f"Feature {index} must have type 'Feature'")

        geometry = feature.get("geometry")
        if geometry:
            geom_type = geometry.get("type")
            coords = geometry.get("coordinates")

            if not geom_type or not coords:
                raise GeometryValidationError(f"Feature {index} has invalid geometry")

            # Basic coordinate validation
            if geom_type == "Point":
                if not isinstance(coords, list) or len(coords) != 2:
                    raise GeometryValidationError(
                        f"Feature {index} has invalid Point coordinates"
                    )
            elif geom_type == "LineString":
                if not isinstance(coords, list) or len(coords) < 2:
                    raise GeometryValidationError(
                        f"Feature {index} has invalid LineString coordinates"
                    )
            elif geom_type == "Polygon":
                if not isinstance(coords, list) or len(coords) < 1:
                    raise GeometryValidationError(
                        f"Feature {index} has invalid Polygon coordinates - no rings"
                    )
                # Validate first ring (exterior ring)
                if not isinstance(coords[0], list) or len(coords[0]) < 3:
                    raise GeometryValidationError(
                        f"Feature {index} has invalid Polygon coordinates - exterior ring must have at least 3 points"
                    )

    def _count_features(self, geojson_path: Path) -> int:
        """
        Count features in GeoJSON file efficiently.

        Args:
            geojson_path: Path to GeoJSON file

        Returns:
            Number of features
        """
        try:
            with open(geojson_path, encoding="utf-8") as f:
                data = json.load(f)

            if data.get("type") == "FeatureCollection":
                return len(data.get("features", []))
            elif data.get("type") == "Feature":
                return 1
            else:
                return 0

        except Exception as e:
            logger.warning(f"Could not count features in {geojson_path}: {e}")
            return 0

    def get_extraction_info(self, feature_types: list[FeatureType]) -> dict[str, Any]:
        """
        Get information about what would be extracted.

        Args:
            feature_types: Feature types to analyze

        Returns:
            Dictionary with extraction information
        """
        return {
            "feature_types": [ft.value for ft in feature_types],
            "tag_mappings": {
                ft.value: self._get_tag_filters(ft) for ft in feature_types
            },
            "output_directory": str(self.output_dir),
            "temp_directory": str(self.temp_dir),
            "cache_enabled": self.cache_manager.enabled,
            "max_retries": self.MAX_RETRIES,
            "chunk_size": self.CHUNK_SIZE,
            "memory_limit_mb": self.MEMORY_LIMIT_MB,
        }

    def cleanup_temp_files(self) -> None:
        """Clean up temporary extraction files."""
        try:
            if self.temp_dir.exists():
                for file_path in self.temp_dir.glob("*.geojson"):
                    if file_path.is_file():
                        file_path.unlink()
                        logger.debug(f"Cleaned up temp file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup temp files: {e}")
