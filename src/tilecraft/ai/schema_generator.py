"""
Schema generation for vector tiles.
"""

import logging
from typing import Any

from tilecraft.models.config import FeatureType, TilecraftConfig
from tilecraft.models.schemas import (
    AttributeType,
    FeatureAttributes,
    GeometryType,
    LayerSchema,
    TileSchema,
)

logger = logging.getLogger(__name__)


class SchemaGenerator:
    """Generates optimized vector tile schemas for OSM features."""

    def __init__(self, config: TilecraftConfig):
        """
        Initialize schema generator.

        Args:
            config: Tilecraft configuration
        """
        self.config = config

    def generate(self, feature_types: list[FeatureType]) -> dict[str, Any]:
        """
        Generate optimized tile schema for feature types.

        Args:
            feature_types: List of feature types to include

        Returns:
            Generated schema as dictionary
        """
        logger.info(
            f"Generating schema for features: {[f.value for f in feature_types]}"
        )

        try:
            schema = self._generate_optimized_schema(feature_types)

            logger.info("Schema generated successfully")
            return schema.dict()

        except Exception as e:
            logger.error(f"Schema generation failed: {e}")
            # Return fallback schema
            return self._get_fallback_schema(feature_types)

    def _generate_optimized_schema(
        self, feature_types: list[FeatureType]
    ) -> TileSchema:
        """
        Generate optimized schema based on feature types and zoom requirements.

        Args:
            feature_types: Feature types to include

        Returns:
            Optimized tile schema
        """
        layers = []

        for feature_type in feature_types:
            layer = self._create_layer_schema(feature_type)
            layers.append(layer)

        schema = TileSchema(
            name="tilecraft_tiles",
            description=f"Vector tiles for {', '.join([f.value for f in feature_types])}",
            min_zoom=self.config.tiles.min_zoom,
            max_zoom=self.config.tiles.max_zoom,
            layers=layers,
            bounds=[
                self.config.bbox.west,
                self.config.bbox.south,
                self.config.bbox.east,
                self.config.bbox.north,
            ],
        )

        return schema

    def _create_layer_schema(self, feature_type: FeatureType) -> LayerSchema:
        """
        Create layer schema for feature type.

        Args:
            feature_type: Feature type

        Returns:
            Layer schema
        """
        # Define geometry types and attributes for each feature
        schema_map = {
            FeatureType.RIVERS: {
                "geometry": GeometryType.LINESTRING,
                "attributes": [
                    FeatureAttributes(
                        name="name", type=AttributeType.STRING, description="River name"
                    ),
                    FeatureAttributes(
                        name="waterway",
                        type=AttributeType.STRING,
                        description="Waterway type",
                    ),
                ],
            },
            FeatureType.FOREST: {
                "geometry": GeometryType.POLYGON,
                "attributes": [
                    FeatureAttributes(
                        name="name",
                        type=AttributeType.STRING,
                        description="Forest name",
                    ),
                    FeatureAttributes(
                        name="natural",
                        type=AttributeType.STRING,
                        description="Natural feature type",
                    ),
                    FeatureAttributes(
                        name="landuse",
                        type=AttributeType.STRING,
                        description="Land use type",
                    ),
                ],
            },
            FeatureType.WATER: {
                "geometry": GeometryType.POLYGON,
                "attributes": [
                    FeatureAttributes(
                        name="name",
                        type=AttributeType.STRING,
                        description="Water body name",
                    ),
                    FeatureAttributes(
                        name="natural",
                        type=AttributeType.STRING,
                        description="Natural feature type",
                    ),
                ],
            },
            FeatureType.LAKES: {
                "geometry": GeometryType.POLYGON,
                "attributes": [
                    FeatureAttributes(
                        name="name", type=AttributeType.STRING, description="Lake name"
                    ),
                    FeatureAttributes(
                        name="water",
                        type=AttributeType.STRING,
                        description="Water type",
                    ),
                ],
            },
            FeatureType.PARKS: {
                "geometry": GeometryType.POLYGON,
                "attributes": [
                    FeatureAttributes(
                        name="name", type=AttributeType.STRING, description="Park name"
                    ),
                    FeatureAttributes(
                        name="leisure",
                        type=AttributeType.STRING,
                        description="Leisure type",
                    ),
                ],
            },
            FeatureType.ROADS: {
                "geometry": GeometryType.LINESTRING,
                "attributes": [
                    FeatureAttributes(
                        name="name", type=AttributeType.STRING, description="Road name"
                    ),
                    FeatureAttributes(
                        name="highway",
                        type=AttributeType.STRING,
                        description="Highway type",
                    ),
                ],
            },
            FeatureType.BUILDINGS: {
                "geometry": GeometryType.POLYGON,
                "attributes": [
                    FeatureAttributes(
                        name="building",
                        type=AttributeType.STRING,
                        description="Building type",
                    ),
                    FeatureAttributes(
                        name="height",
                        type=AttributeType.NUMBER,
                        description="Building height",
                    ),
                ],
            },
        }

        config = schema_map.get(
            feature_type, {"geometry": GeometryType.POINT, "attributes": []}
        )

        # Determine appropriate zoom levels
        min_zoom, max_zoom = self._get_feature_zoom_levels(feature_type)

        return LayerSchema(
            name=feature_type.value,
            geometry_type=config["geometry"],
            min_zoom=min_zoom,
            max_zoom=max_zoom,
            attributes=config["attributes"],
            description=f"Layer containing {feature_type.value} features",
        )

    def _get_feature_zoom_levels(self, feature_type: FeatureType) -> tuple[int, int]:
        """
        Get appropriate zoom levels for feature type.

        Args:
            feature_type: Feature type

        Returns:
            Tuple of (min_zoom, max_zoom)
        """
        zoom_map = {
            FeatureType.RIVERS: (6, 14),
            FeatureType.FOREST: (4, 12),
            FeatureType.WATER: (4, 14),
            FeatureType.LAKES: (4, 14),
            FeatureType.PARKS: (8, 16),
            FeatureType.ROADS: (8, 18),
            FeatureType.BUILDINGS: (12, 18),
        }

        feature_min, feature_max = zoom_map.get(feature_type, (0, 14))

        # Constrain to global zoom levels
        min_zoom = max(self.config.tiles.min_zoom, feature_min)
        max_zoom = min(self.config.tiles.max_zoom, feature_max)

        return min_zoom, max_zoom

    def _get_fallback_schema(self, feature_types: list[FeatureType]) -> dict[str, Any]:
        """
        Get fallback schema when AI generation fails.

        Args:
            feature_types: Feature types

        Returns:
            Fallback schema as dictionary
        """
        return {
            "name": "fallback_schema",
            "description": "Fallback schema when AI generation fails",
            "layers": [
                {
                    "name": feature_type.value,
                    "geometry_type": "polygon",
                    "min_zoom": self.config.tiles.min_zoom,
                    "max_zoom": self.config.tiles.max_zoom,
                    "attributes": [],
                }
                for feature_type in feature_types
            ],
        }

    def _call_ai_api(self, prompt: str) -> str:
        """
        Call AI API to generate schema.

        Args:
            prompt: Prompt for AI

        Returns:
            AI response
        """
        # Schema generation is now deterministic based on feature types
        logger.debug("Schema generation uses optimized deterministic rules")
        return ""
