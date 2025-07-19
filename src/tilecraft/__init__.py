"""
Tilecraft: Streamlined CLI for OSM Vector Tile Generation

A command-line tool that ingests OpenStreetMap (OSM) data for specified bounding boxes
and natural features, processes it, and outputs Mapbox Vector Tiles (MBTiles) and 
MapLibre GL JS-compatible style JSON files with smart caching and optimized processing.
"""

__version__ = "0.1.0"
__author__ = "Richard"
__email__ = "richard@example.com"

from .models.config import BoundingBox, FeatureConfig, OutputConfig, PaletteConfig

__all__ = [
    "__version__",
    "BoundingBox", 
    "FeatureConfig",
    "OutputConfig",
    "PaletteConfig",
] 