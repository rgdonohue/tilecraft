"""
Main processing pipeline for Tilecraft.
"""

import logging
from pathlib import Path
from typing import Any

from tilecraft.ai.schema_generator import SchemaGenerator
from tilecraft.ai.style_generator import StyleGenerator
from tilecraft.core.feature_extractor import FeatureExtractor
from tilecraft.core.osm_downloader import OSMDownloader
from tilecraft.core.tile_generator import TileGenerator
from tilecraft.models.config import TilecraftConfig
from tilecraft.utils.cache import CacheManager
from tilecraft.utils.validation import validate_osm_data


class TilecraftPipeline:
    """Main processing pipeline for vector tile generation."""

    def __init__(self, config: TilecraftConfig):
        """Initialize pipeline with configuration."""
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Set up logging
        log_level = logging.DEBUG if config.verbose else logging.INFO
        logging.basicConfig(level=log_level)

        # Initialize components
        self.cache_manager = CacheManager(
            config.output.cache_dir, enabled=config.cache_enabled
        )
        self.osm_downloader = OSMDownloader(config, self.cache_manager)
        self.feature_extractor = FeatureExtractor(config, self.cache_manager)
        self.tile_generator = TileGenerator(config, self.cache_manager)
        self.schema_generator = SchemaGenerator(config)
        self.style_generator = StyleGenerator(config)

        # Create output directories
        config.output.create_directories()

    def run(self) -> dict[str, Any]:
        """Run the complete pipeline."""
        self.logger.info("Starting Tilecraft pipeline")

        try:
            # Step 1: Download OSM data
            osm_data_path = self.download_osm_data()

            # Step 2: Extract features
            feature_files = self.extract_features(osm_data_path)

            # Step 3: Generate AI schema
            schema = self.generate_schema()

            # Step 4: Generate vector tiles
            tiles_path = self.generate_tiles(feature_files)

            # Step 5: Generate style
            style_path = self.generate_style(schema)

            result = {
                "osm_data": osm_data_path,
                "features": feature_files,
                "schema": schema,
                "tiles": tiles_path,
                "style": style_path,
            }

            self.logger.info("Pipeline completed successfully")
            return result

        except Exception as e:
            self.logger.error(f"Pipeline failed: {e}")
            raise

    def download_osm_data(self) -> Path:
        """Download and validate OSM data."""
        self.logger.info(
            f"Downloading OSM data for bbox: {self.config.bbox.to_string()}"
        )

        osm_data_path = self.osm_downloader.download(self.config.bbox)

        # Validate downloaded data
        if not validate_osm_data(osm_data_path):
            raise ValueError(f"Invalid OSM data downloaded: {osm_data_path}")

        self.logger.info(f"OSM data downloaded: {osm_data_path}")
        return osm_data_path

    def extract_features(self, osm_data_path: Path) -> dict[str, Path]:
        """Extract features from OSM data."""
        self.logger.info(
            f"Extracting features: {[f.value for f in self.config.features.types]}"
        )

        feature_files = self.feature_extractor.extract(
            osm_data_path, self.config.features.types
        )

        # Log extraction results
        for feature_type, file_path in feature_files.items():
            self.logger.info(f"Extracted {feature_type}: {file_path}")

        return feature_files

    def generate_schema(self) -> dict[str, Any]:
        """Generate optimized vector tile schema."""
        self.logger.info("Generating optimized tile schema")

        schema = self.schema_generator.generate(self.config.features.types)

        # Save schema to file
        schema_path = self.config.output.data_dir / "schema.json"
        with open(schema_path, "w") as f:
            import json

            json.dump(schema, f, indent=2)

        self.logger.info(f"Schema generated: {schema_path}")
        return schema

    def generate_tiles(self, feature_files: dict[str, Path]) -> Path:
        """Generate vector tiles from feature files."""
        self.logger.info("Generating vector tiles")

        tiles_path = self.tile_generator.generate(feature_files)

        self.logger.info(f"Vector tiles generated: {tiles_path}")
        return tiles_path

    def generate_style(self, schema: dict[str, Any]) -> Path:
        """Generate MapLibre style with palette theming."""
        self.logger.info("Generating MapLibre style with palette theming")

        style_path = self.style_generator.generate(schema, self.config.palette)

        self.logger.info(f"Style generated: {style_path}")
        return style_path
    
    def cleanup(self) -> None:
        """Clean up all pipeline components and resources."""
        try:
            self.logger.debug("Starting pipeline cleanup")
            
            # Clean up feature extractor
            if hasattr(self, 'feature_extractor'):
                self.feature_extractor.cleanup_temp_files()
            
            # Clean up tile generator
            if hasattr(self, 'tile_generator'):
                self.tile_generator.cleanup_temp_files()
            
            # Clean up cache manager
            if hasattr(self, 'cache_manager'):
                # Cache manager cleanup if needed
                pass
            
            # Close any open file handles or database connections
            # This ensures no lingering processes or file locks
            
            self.logger.debug("Pipeline cleanup completed")
        except Exception as e:
            self.logger.warning(f"Error during pipeline cleanup: {e}")
