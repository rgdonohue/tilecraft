"""
Data validation utilities.
"""

import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def validate_osm_data(file_path: Path) -> bool:
    """
    Validate OSM data file.

    Args:
        file_path: Path to OSM data file

    Returns:
        True if valid, False otherwise
    """
    if not file_path.exists():
        logger.error(f"OSM file does not exist: {file_path}")
        return False

    if file_path.stat().st_size == 0:
        logger.error(f"OSM file is empty: {file_path}")
        return False

    # Check file format
    if file_path.suffix.lower() in [".pbf"]:
        return _validate_pbf_file(file_path)
    elif file_path.suffix.lower() in [".osm", ".xml"]:
        return _validate_osm_xml_file(file_path)
    else:
        logger.warning(f"Unknown OSM file format: {file_path}")
        return False


def _validate_pbf_file(file_path: Path) -> bool:
    """Validate PBF file format."""
    try:
        # Try to read header to validate format
        with open(file_path, "rb") as f:
            header = f.read(4)
            # PBF files should start with specific bytes
            if len(header) < 4:
                return False
        return True
    except Exception as e:
        logger.error(f"Error validating PBF file {file_path}: {e}")
        return False


def _validate_osm_xml_file(file_path: Path) -> bool:
    """Validate OSM XML file format."""
    try:
        with open(file_path, encoding="utf-8") as f:
            first_line = f.readline().strip()
            if not first_line.startswith("<?xml"):
                return False

            # Check for OSM root element
            content = f.read(1000)  # Read first 1KB
            if "<osm" not in content:
                return False

        return True
    except Exception as e:
        logger.error(f"Error validating OSM XML file {file_path}: {e}")
        return False


def validate_geojson(file_path: Path) -> bool:
    """
    Validate GeoJSON file.

    Args:
        file_path: Path to GeoJSON file

    Returns:
        True if valid, False otherwise
    """
    if not file_path.exists():
        logger.error(f"GeoJSON file does not exist: {file_path}")
        return False

    try:
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)

        return _validate_geojson_structure(data)

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error validating GeoJSON {file_path}: {e}")
        return False


def _validate_geojson_structure(data: dict) -> bool:
    """Validate GeoJSON structure."""
    if not isinstance(data, dict):
        return False

    if "type" not in data:
        return False

    geojson_type = data["type"]

    if geojson_type == "FeatureCollection":
        if "features" not in data:
            return False
        if not isinstance(data["features"], list):
            return False

        # Validate each feature
        for feature in data["features"]:
            if not _validate_geojson_feature(feature):
                return False

    elif geojson_type == "Feature":
        return _validate_geojson_feature(data)

    elif geojson_type in [
        "Point",
        "LineString",
        "Polygon",
        "MultiPoint",
        "MultiLineString",
        "MultiPolygon",
    ]:
        return _validate_geojson_geometry(data)

    else:
        logger.warning(f"Unknown GeoJSON type: {geojson_type}")
        return False

    return True


def _validate_geojson_feature(feature: dict) -> bool:
    """Validate GeoJSON feature."""
    if not isinstance(feature, dict):
        return False

    if feature.get("type") != "Feature":
        return False

    # Must have geometry (can be null)
    if "geometry" not in feature:
        return False

    geometry = feature["geometry"]
    if geometry is not None:
        if not _validate_geojson_geometry(geometry):
            return False

    return True


def _validate_geojson_geometry(geometry: dict) -> bool:
    """Validate GeoJSON geometry."""
    if not isinstance(geometry, dict):
        return False

    if "type" not in geometry or "coordinates" not in geometry:
        return False

    coordinates = geometry["coordinates"]

    # Basic coordinate validation
    if not isinstance(coordinates, list):
        return False

    if len(coordinates) == 0:
        return False

    # Type-specific validation could be added here
    return True


def validate_mbtiles(file_path: Path) -> bool:
    """
    Validate MBTiles file.

    Args:
        file_path: Path to MBTiles file

    Returns:
        True if valid, False otherwise
    """
    if not file_path.exists():
        logger.error(f"MBTiles file does not exist: {file_path}")
        return False

    try:
        import sqlite3

        with sqlite3.connect(file_path) as conn:
            cursor = conn.cursor()

            # Check required tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            required_tables = ["metadata", "tiles"]
            for table in required_tables:
                if table not in tables:
                    logger.error(f"Missing required table in MBTiles: {table}")
                    return False

            # Check metadata
            cursor.execute("SELECT COUNT(*) FROM metadata")
            if cursor.fetchone()[0] == 0:
                logger.warning("MBTiles metadata table is empty")

            # Check tiles
            cursor.execute("SELECT COUNT(*) FROM tiles")
            if cursor.fetchone()[0] == 0:
                logger.warning("MBTiles contains no tiles")
                return False

        return True

    except Exception as e:
        logger.error(f"Error validating MBTiles {file_path}: {e}")
        return False


def count_features(geojson_path: Path) -> Optional[int]:
    """
    Count features in GeoJSON file.

    Args:
        geojson_path: Path to GeoJSON file

    Returns:
        Number of features or None if error
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
        logger.error(f"Error counting features in {geojson_path}: {e}")
        return None
