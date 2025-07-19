"""
Data validation utilities.
"""

import logging
from pathlib import Path

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
    suffix = file_path.suffix.lower()
    if suffix == ".pbf":
        return _validate_pbf_file(file_path)
    elif suffix in [".osm", ".xml"]:
        return _validate_osm_xml_file(file_path)
    else:
        logger.warning(f"Unknown OSM file format: {file_path}")
        return False


def _validate_pbf_file(file_path: Path) -> bool:
    """Validate PBF file format with basic header check."""
    try:
        with open(file_path, "rb") as f:
            header = f.read(4)
            return len(header) == 4  # Simple existence check
    except Exception as e:
        logger.error(f"Error validating PBF file {file_path}: {e}")
        return False


def _validate_osm_xml_file(file_path: Path) -> bool:
    """Validate OSM XML file format with basic structure check."""
    try:
        with open(file_path, encoding="utf-8") as f:
            first_line = f.readline().strip()
            if not first_line.startswith("<?xml"):
                return False
            
            # Quick check for OSM content in first 1KB
            content = f.read(1000)
            return "<osm" in content
            
    except Exception as e:
        logger.error(f"Error validating OSM XML file {file_path}: {e}")
        return False
