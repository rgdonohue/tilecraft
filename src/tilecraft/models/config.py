"""
Configuration models using Pydantic for type safety and validation.
"""

from enum import Enum
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from pydantic_settings import BaseSettings


class FeatureType(str, Enum):
    """Supported OSM feature types."""

    # Water Features
    RIVERS = "rivers"
    WATER = "water"
    LAKES = "lakes"
    WETLANDS = "wetlands"
    WATERWAYS = "waterways"
    COASTLINE = "coastline"
    
    # Natural Features
    FOREST = "forest"
    WOODS = "woods"
    MOUNTAINS = "mountains"
    PEAKS = "peaks"
    CLIFFS = "cliffs"
    BEACHES = "beaches"
    GLACIERS = "glaciers"
    VOLCANOES = "volcanoes"
    
    # Land Use
    PARKS = "parks"
    FARMLAND = "farmland"
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    INDUSTRIAL = "industrial"
    MILITARY = "military"
    CEMETERIES = "cemeteries"
    
    # Transportation
    ROADS = "roads"
    HIGHWAYS = "highways"
    RAILWAYS = "railways"
    AIRPORTS = "airports"
    BRIDGES = "bridges"
    TUNNELS = "tunnels"
    PATHS = "paths"
    CYCLEWAYS = "cycleways"
    
    # Built Environment  
    BUILDINGS = "buildings"
    CHURCHES = "churches"
    SCHOOLS = "schools"
    HOSPITALS = "hospitals"
    UNIVERSITIES = "universities"
    
    # Amenities
    RESTAURANTS = "restaurants"
    SHOPS = "shops"
    HOTELS = "hotels"
    BANKS = "banks"
    FUEL_STATIONS = "fuel_stations"
    POST_OFFICES = "post_offices"
    
    # Recreation
    PLAYGROUNDS = "playgrounds"
    SPORTS_FIELDS = "sports_fields"
    GOLF_COURSES = "golf_courses"
    STADIUMS = "stadiums"
    SWIMMING_POOLS = "swimming_pools"
    
    # Infrastructure
    POWER_LINES = "power_lines"
    WIND_TURBINES = "wind_turbines"
    SOLAR_FARMS = "solar_farms"
    DAMS = "dams"
    BARRIERS = "barriers"
    
    # Administrative
    BOUNDARIES = "boundaries"
    PROTECTED_AREAS = "protected_areas"


class BoundingBox(BaseModel):
    """Bounding box coordinates with validation."""

    west: float = Field(..., ge=-180, le=180, description="Western longitude")
    south: float = Field(..., ge=-90, le=90, description="Southern latitude")
    east: float = Field(..., ge=-180, le=180, description="Eastern longitude")
    north: float = Field(..., ge=-90, le=90, description="Northern latitude")

    @model_validator(mode="after")
    def validate_coordinates(self):
        """Ensure coordinate order is correct."""
        if self.east <= self.west:
            raise ValueError("Eastern longitude must be greater than western longitude")
        if self.north <= self.south:
            raise ValueError("Northern latitude must be greater than southern latitude")
        return self

    @property
    def area_degrees(self) -> float:
        """Calculate bounding box area in square degrees."""
        return (self.east - self.west) * (self.north - self.south)

    @property
    def center(self) -> tuple[float, float]:
        """Get center point (lon, lat)."""
        return ((self.west + self.east) / 2, (self.south + self.north) / 2)

    def to_string(self) -> str:
        """Convert to comma-separated string format."""
        return f"{self.west},{self.south},{self.east},{self.north}"

    @classmethod
    def from_string(cls, bbox_str: str) -> "BoundingBox":
        """Parse from comma-separated string format."""
        try:
            coords = [float(x.strip()) for x in bbox_str.split(",")]
            if len(coords) != 4:
                raise ValueError(f"Expected 4 coordinates, got {len(coords)}")
            return cls(west=coords[0], south=coords[1], east=coords[2], north=coords[3])
        except (ValueError, IndexError) as e:
            raise ValueError(
                f"Invalid bounding box format: {bbox_str}. Expected 'west,south,east,north'"
            ) from e


class FeatureConfig(BaseModel):
    """Configuration for OSM feature extraction."""

    types: list[FeatureType] = Field(
        ..., min_length=1, description="Feature types to extract"
    )
    custom_tags: Optional[dict[str, list[str]]] = Field(
        default=None, description="Custom OSM tag mappings for feature types"
    )

    @field_validator("types", mode="before")
    @classmethod
    def parse_feature_types(cls, v):
        """Parse feature types from strings."""
        if isinstance(v, str):
            return [FeatureType(feat.strip().lower()) for feat in v.split(",")]
        elif isinstance(v, list):
            return [
                FeatureType(feat.strip().lower()) if isinstance(feat, str) else feat
                for feat in v
            ]
        return v


class PaletteConfig(BaseModel):
    """Style palette configuration."""

    name: str = Field(..., description="Palette name (e.g., 'subalpine dusk')")
    colors: Optional[dict[str, str]] = Field(
        default=None, description="Custom color mappings for features"
    )
    mood: Optional[str] = Field(
        default=None, description="Style mood description for AI generation"
    )

    @field_validator("colors")
    @classmethod
    def validate_hex_colors(cls, v):
        """Validate hex color format."""
        if v is None:
            return v
        for feature, color in v.items():
            if not color.startswith("#") or len(color) not in [4, 7]:
                raise ValueError(f"Invalid hex color for {feature}: {color}")
        return v


class OutputConfig(BaseModel):
    """Output directory and file configuration."""

    base_dir: Path = Field(default=Path("output"), description="Base output directory")
    name: Optional[str] = Field(
        default=None, description="Project name for file naming"
    )

    # Directory structure
    tiles_dir: Optional[Path] = Field(
        default=None, description="Tiles output directory"
    )
    styles_dir: Optional[Path] = Field(
        default=None, description="Styles output directory"
    )
    data_dir: Optional[Path] = Field(default=None, description="GeoJSON data directory")
    cache_dir: Optional[Path] = Field(default=None, description="Cache directory")

    @model_validator(mode="after")
    def set_default_directories(self):
        """Set default directory structure."""
        if self.tiles_dir is None:
            self.tiles_dir = self.base_dir / "tiles"
        if self.styles_dir is None:
            self.styles_dir = self.base_dir / "styles"
        if self.data_dir is None:
            self.data_dir = self.base_dir / "data"
        if self.cache_dir is None:
            self.cache_dir = self.base_dir / "cache"

        return self

    def create_directories(self) -> None:
        """Create all output directories."""
        for dir_path in [
            self.tiles_dir,
            self.styles_dir,
            self.data_dir,
            self.cache_dir,
        ]:
            if dir_path:
                dir_path.mkdir(parents=True, exist_ok=True)


# Legacy configuration class - will be removed in future version
class AIConfig(BaseModel):
    """Legacy AI configuration - deprecated."""

    provider: str = Field(default="openai", description="Legacy AI provider setting")
    model: str = Field(default="gpt-4", description="Legacy model name")
    api_key: Optional[str] = Field(default=None, description="Legacy API key")
    max_tokens: int = Field(default=2000, description="Legacy max tokens")
    temperature: float = Field(
        default=0.3, ge=0, le=2, description="Legacy temperature"
    )


class TileConfig(BaseModel):
    """Vector tile generation configuration."""

    min_zoom: int = Field(default=0, ge=0, le=24, description="Minimum zoom level")
    max_zoom: int = Field(default=14, ge=0, le=24, description="Maximum zoom level")
    buffer: int = Field(default=64, description="Tile buffer in pixels")
    detail: int = Field(default=12, ge=7, le=15, description="Tile detail level (7-15)")
    simplification: float = Field(
        default=1.0, description="Geometry simplification factor"
    )

    # Advanced tippecanoe options
    drop_rate: float = Field(
        default=2.5, description="Feature drop rate for zoom level scaling"
    )
    base_zoom: int = Field(
        default=14, ge=0, le=24, description="Base zoom level for feature calculation"
    )
    no_feature_limit: bool = Field(
        default=True, description="Disable feature limit per tile"
    )
    no_tile_size_limit: bool = Field(
        default=True, description="Disable tile size limit"
    )
    force_feature_limit: Optional[int] = Field(
        default=None, description="Force specific feature limit"
    )

    # Performance settings
    maximum_tile_bytes: Optional[int] = Field(
        default=None, description="Maximum bytes per tile"
    )
    maximum_tile_features: Optional[int] = Field(
        default=None, description="Maximum features per tile"
    )
    simplification_at_max_zoom: float = Field(
        default=0.0, description="Simplification at maximum zoom"
    )

    # Layer-specific configurations
    layer_configs: Optional[dict[str, dict[str, Any]]] = Field(
        default=None, description="Feature-type specific tile configurations"
    )

    # Quality profiles
    quality_profile: str = Field(
        default="balanced",
        description="Quality profile: fast, balanced, or high_quality",
    )

    # Processing options
    parallel_processing: bool = Field(
        default=True, description="Enable parallel layer processing"
    )
    temp_dir: Optional[Path] = Field(
        default=None, description="Temporary directory for processing"
    )

    @model_validator(mode="after")
    def validate_zoom_order(self):
        """Ensure max_zoom >= min_zoom."""
        if self.max_zoom < self.min_zoom:
            raise ValueError("Maximum zoom must be >= minimum zoom")
        if self.base_zoom > self.max_zoom:
            raise ValueError("Base zoom must be <= maximum zoom")
        return self

    @model_validator(mode="after")
    def set_layer_defaults(self):
        """Set default layer configurations based on feature types."""
        if self.layer_configs is None:
            self.layer_configs = {
                "rivers": {
                    "min_zoom": 6,
                    "max_zoom": self.max_zoom,
                    "simplification": 0.5,
                    "drop_rate": 1.5,
                },
                "roads": {
                    "min_zoom": 8,
                    "max_zoom": self.max_zoom,
                    "simplification": 0.8,
                    "drop_rate": 2.0,
                },
                "buildings": {
                    "min_zoom": 12,
                    "max_zoom": self.max_zoom,
                    "simplification": 0.1,
                    "drop_rate": 3.0,
                },
                "forest": {
                    "min_zoom": 4,
                    "max_zoom": self.max_zoom - 2,
                    "simplification": 1.0,
                    "drop_rate": 2.5,
                },
                "water": {
                    "min_zoom": 0,
                    "max_zoom": self.max_zoom,
                    "simplification": 0.3,
                    "drop_rate": 1.0,
                },
                "lakes": {
                    "min_zoom": 4,
                    "max_zoom": self.max_zoom,
                    "simplification": 0.3,
                    "drop_rate": 1.5,
                },
                "wetlands": {
                    "min_zoom": 6,
                    "max_zoom": self.max_zoom - 1,
                    "simplification": 0.8,
                    "drop_rate": 2.0,
                },
                "parks": {
                    "min_zoom": 8,
                    "max_zoom": self.max_zoom,
                    "simplification": 0.5,
                    "drop_rate": 2.0,
                },
            }
        return self

    def get_layer_config(self, feature_type: str) -> dict[str, Any]:
        """Get configuration for specific feature type."""
        return self.layer_configs.get(
            feature_type,
            {
                "min_zoom": self.min_zoom,
                "max_zoom": self.max_zoom,
                "simplification": self.simplification,
                "drop_rate": self.drop_rate,
            },
        )

    def get_quality_settings(self) -> dict[str, Any]:
        """Get settings based on quality profile."""
        profiles = {
            "fast": {
                "simplification": 2.0,
                "drop_rate": 4.0,
                "no_feature_limit": True,
                "no_tile_size_limit": True,
            },
            "balanced": {
                "simplification": 1.0,
                "drop_rate": 2.5,
                "no_feature_limit": True,
                "no_tile_size_limit": False,
            },
            "high_quality": {
                "simplification": 0.5,
                "drop_rate": 1.5,
                "no_feature_limit": False,
                "no_tile_size_limit": False,
            },
        }
        return profiles.get(self.quality_profile, profiles["balanced"])


class TilecraftConfig(BaseSettings):
    """Main configuration class."""

    model_config = ConfigDict(
        env_prefix="TILECRAFT_", env_file=".env", case_sensitive=False, extra="forbid"
    )

    bbox: BoundingBox
    features: FeatureConfig
    palette: PaletteConfig
    output: OutputConfig = Field(default_factory=OutputConfig)
    # ai: AIConfig = Field(default_factory=AIConfig)  # Deprecated - will be removed
    tiles: TileConfig = Field(default_factory=TileConfig)

    # Processing options
    cache_enabled: bool = Field(default=True, description="Enable caching")
    verbose: bool = Field(default=False, description="Verbose output")

    @model_validator(mode="before")
    @classmethod
    def handle_openai_api_key(cls, values):
        """Handle OPENAI_API_KEY environment variable mapping to ai.api_key."""
        if isinstance(values, dict):
            # If we have openai_api_key from env vars, map it to ai.api_key
            if "openai_api_key" in values:
                if "ai" not in values:
                    values["ai"] = {}
                if isinstance(values["ai"], dict) and "api_key" not in values["ai"]:
                    values["ai"]["api_key"] = values.pop("openai_api_key")
                else:
                    # Remove the extra field to prevent validation error
                    values.pop("openai_api_key", None)
        return values
