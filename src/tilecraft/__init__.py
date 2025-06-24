"""
Tilecraft: AI-Assisted CLI Tool for Vector Tile Generation from OSM

A command-line tool that ingests OpenStreetMap (OSM) data for specified bounding boxes
and natural features, processes it, and outputs Mapbox Vector Tiles (MBTiles) and 
MapLibre GL JS-compatible style JSON files using AI assistance.
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