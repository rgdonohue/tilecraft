"""
MapLibre GL JS style generation.
"""

import json
import logging
from pathlib import Path
from typing import Any

from tilecraft.models.config import PaletteConfig, TilecraftConfig

logger = logging.getLogger(__name__)


class StyleGenerator:
    """Generates optimized MapLibre GL JS styles with palette-based theming."""

    def __init__(self, config: TilecraftConfig):
        """
        Initialize style generator.

        Args:
            config: Tilecraft configuration
        """
        self.config = config

    def generate(self, schema: dict[str, Any], palette: PaletteConfig) -> Path:
        """
        Generate MapLibre style for schema and palette.

        Args:
            schema: Tile schema
            palette: Palette configuration

        Returns:
            Path to generated style JSON file
        """
        logger.info(f"Generating MapLibre style with palette: {palette.name}")

        try:
            # Generate style
            style = self._generate_default_style(schema, palette)

            # Save to file
            output_path = self._save_style(style, palette.name)

            logger.info(f"Style generated: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Style generation failed: {e}")
            raise

    def _generate_default_style(
        self, schema: dict[str, Any], palette: PaletteConfig
    ) -> dict[str, Any]:
        """
        Generate default MapLibre style.

        Args:
            schema: Tile schema
            palette: Palette configuration

        Returns:
            MapLibre style as dictionary
        """
        # Get base colors for palette
        colors = self._get_palette_colors(palette.name)

        # Base style structure
        style = {
            "version": 8,
            "name": f"Tilecraft - {palette.name}",
            "metadata": {
                "tilecraft:palette": palette.name,
                "tilecraft:generated": True,
            },
            "sources": {
                "tilecraft": {
                    "type": "vector",
                    "url": f"mbtiles://{self.config.output.name or 'tileset'}.mbtiles",
                }
            },
            "layers": [],
        }

        # Add background layer
        style["layers"].append(
            {
                "id": "background",
                "type": "background",
                "paint": {"background-color": colors["background"]},
            }
        )

        # Add layers for each feature type
        for layer_info in schema.get("layers", []):
            layer_name = layer_info["name"]
            geometry_type = layer_info.get("geometry_type", "polygon")

            style_layer = self._create_style_layer(
                layer_name, geometry_type, colors, layer_info
            )

            if style_layer:
                style["layers"].append(style_layer)

        return style

    def _create_style_layer(
        self,
        layer_name: str,
        geometry_type: str,
        colors: dict[str, str],
        layer_info: dict,
    ) -> dict[str, Any]:
        """
        Create style layer for feature type.

        Args:
            layer_name: Layer name
            geometry_type: Geometry type
            colors: Color palette
            layer_info: Layer information from schema

        Returns:
            MapLibre style layer
        """
        base_layer = {
            "id": layer_name,
            "source": "tilecraft",
            "source-layer": layer_name,
            "minzoom": layer_info.get("min_zoom", 0),
            "maxzoom": layer_info.get("max_zoom", 14),
        }

        if geometry_type == "linestring":
            # Line styling
            base_layer.update(
                {
                    "type": "line",
                    "paint": {
                        "line-color": colors.get(layer_name, colors["default_line"]),
                        "line-width": self._get_line_width(layer_name),
                        "line-opacity": 0.8,
                    },
                }
            )

        elif geometry_type == "polygon":
            # Polygon styling
            base_layer.update(
                {
                    "type": "fill",
                    "paint": {
                        "fill-color": colors.get(layer_name, colors["default_fill"]),
                        "fill-opacity": 0.6,
                        "fill-outline-color": colors.get(
                            f"{layer_name}_outline", colors["outline"]
                        ),
                    },
                }
            )

        elif geometry_type == "point":
            # Point styling
            base_layer.update(
                {
                    "type": "circle",
                    "paint": {
                        "circle-color": colors.get(layer_name, colors["default_point"]),
                        "circle-radius": 4,
                        "circle-opacity": 0.8,
                    },
                }
            )

        return base_layer

    def _get_line_width(self, layer_name: str) -> dict[str, Any]:
        """
        Get zoom-dependent line width.

        Args:
            layer_name: Layer name

        Returns:
            MapLibre expression for line width
        """
        width_map = {
            "rivers": ["interpolate", ["linear"], ["zoom"], 6, 1, 10, 2, 14, 4],
            "roads": ["interpolate", ["linear"], ["zoom"], 8, 0.5, 12, 1, 16, 3],
            "default": ["interpolate", ["linear"], ["zoom"], 6, 1, 14, 2],
        }

        return width_map.get(layer_name, width_map["default"])

    def _get_palette_colors(self, palette_name: str) -> dict[str, str]:
        """
        Get color palette for style.

        Args:
            palette_name: Palette name

        Returns:
            Dictionary of colors
        """
        palettes = {
            "subalpine dusk": {
                "background": "#2C3E50",
                "rivers": "#00D4FF",
                "forest": "#2E8B57",
                "water": "#4A90E2",
                "lakes": "#1E88E5",
                "parks": "#8BC34A",
                "roads": "#95A5A6",
                "buildings": "#7F8C8D",
                "outline": "#34495E",
                "default_line": "#3498DB",
                "default_fill": "#27AE60",
                "default_point": "#E74C3C",
            },
            "desert sunset": {
                "background": "#FFA726",
                "rivers": "#42A5F5",
                "forest": "#8BC34A",
                "water": "#1E88E5",
                "lakes": "#1976D2",
                "parks": "#4CAF50",
                "roads": "#8D6E63",
                "buildings": "#6D4C41",
                "outline": "#5D4037",
                "default_line": "#FF7043",
                "default_fill": "#FF8A65",
                "default_point": "#F44336",
            },
            "urban midnight": {
                "background": "#0D1117",
                "rivers": "#58A6FF",
                "forest": "#238636",
                "water": "#1F6FEB",
                "lakes": "#0969DA",
                "parks": "#2DA44E",
                "roads": "#F0F6FC",
                "buildings": "#8B949E",
                "outline": "#30363D",
                "default_line": "#58A6FF",
                "default_fill": "#21262D",
                "default_point": "#F85149",
            },
        }

        return palettes.get(palette_name.lower(), palettes["subalpine dusk"])

    def _save_style(self, style: dict[str, Any], palette_name: str) -> Path:
        """
        Save style to JSON file.

        Args:
            style: Style dictionary
            palette_name: Palette name for filename

        Returns:
            Path to saved file
        """
        # Create filename
        safe_name = palette_name.lower().replace(" ", "_")
        project_name = self.config.output.name or "tileset"
        filename = f"{project_name}_{safe_name}_style.json"

        output_path = self.config.output.styles_dir / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Save JSON
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(style, f, indent=2, ensure_ascii=False)

        return output_path

    def _call_ai_api(self, prompt: str) -> str:
        """
        Call AI API to generate style.

        Args:
            prompt: Prompt for AI

        Returns:
            AI response
        """
        # Style generation is now deterministic based on palette
        logger.debug("Style generation uses optimized palette-based rules")
        return ""
