"""
Vector tile schema definitions.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class GeometryType(str, Enum):
    """Supported geometry types."""

    POINT = "point"
    LINESTRING = "linestring"
    POLYGON = "polygon"


class AttributeType(str, Enum):
    """Attribute data types."""

    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"


class FeatureAttributes(BaseModel):
    """Feature attribute definition."""

    name: str = Field(..., description="Attribute name")
    type: AttributeType = Field(..., description="Attribute data type")
    description: Optional[str] = Field(
        default=None, description="Attribute description"
    )
    required: bool = Field(default=False, description="Whether attribute is required")


class LayerSchema(BaseModel):
    """Vector tile layer schema."""

    name: str = Field(..., description="Layer name")
    geometry_type: GeometryType = Field(..., description="Primary geometry type")
    min_zoom: int = Field(default=0, ge=0, le=24, description="Minimum zoom level")
    max_zoom: int = Field(default=14, ge=0, le=24, description="Maximum zoom level")
    attributes: list[FeatureAttributes] = Field(
        default_factory=list, description="Layer attributes"
    )
    description: Optional[str] = Field(default=None, description="Layer description")

    # Tippecanoe-specific options
    simplification: Optional[float] = Field(
        default=None, description="Geometry simplification"
    )
    buffer: Optional[int] = Field(default=None, description="Tile buffer in pixels")


class TileSchema(BaseModel):
    """Complete vector tile schema."""

    name: str = Field(..., description="Tileset name")
    description: Optional[str] = Field(default=None, description="Tileset description")
    version: str = Field(default="1.0.0", description="Schema version")

    # Zoom configuration
    min_zoom: int = Field(default=0, ge=0, le=24, description="Global minimum zoom")
    max_zoom: int = Field(default=14, ge=0, le=24, description="Global maximum zoom")

    # Layer definitions
    layers: list[LayerSchema] = Field(..., min_items=1, description="Tile layers")

    # Metadata
    attribution: Optional[str] = Field(
        default="© OpenStreetMap contributors", description="Data attribution"
    )
    bounds: Optional[list[float]] = Field(
        default=None, description="Tileset bounds [west, south, east, north]"
    )
    center: Optional[list[float]] = Field(
        default=None, description="Tileset center [lon, lat, zoom]"
    )

    def get_tippecanoe_args(self) -> list[str]:
        """Generate tippecanoe command arguments."""
        args = [
            f"--minimum-zoom={self.min_zoom}",
            f"--maximum-zoom={self.max_zoom}",
        ]

        if self.bounds:
            west, south, east, north = self.bounds
            args.append(f"--clip-bounding-box={west},{south},{east},{north}")

        return args

    def get_layer_by_name(self, name: str) -> Optional[LayerSchema]:
        """Get layer by name."""
        return next((layer for layer in self.layers if layer.name == name), None)
