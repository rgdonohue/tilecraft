#!/usr/bin/env python3
"""
Example demonstrating production-ready vector tile generation with Tilecraft.

This example shows how to use the enhanced TileGenerator with comprehensive
error handling, caching, progress tracking, and validation.
"""

import sys
import logging
from pathlib import Path

# Add src to path for example
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tilecraft.models.config import (
    TilecraftConfig, BoundingBox, FeatureConfig, OutputConfig, 
    PaletteConfig, TileConfig, FeatureType
)
from tilecraft.core.tile_generator import TileGenerator
from tilecraft.utils.cache import CacheManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """Demonstrate tile generation capabilities."""
    
    print("🚀 Tilecraft Production-Ready Tile Generation Example")
    print("=" * 60)
    
    # 1. Create comprehensive configuration
    config = TilecraftConfig(
        bbox=BoundingBox(west=-105.02, south=39.74, east=-105.01, north=39.75),  # Small Boulder area
        features=FeatureConfig(types=[FeatureType.RIVERS, FeatureType.ROADS, FeatureType.BUILDINGS]),
        palette=PaletteConfig(name="mountain_dawn"),
        output=OutputConfig(base_dir=Path("example_output")),
        tiles=TileConfig(
            min_zoom=10,
            max_zoom=16,
            quality_profile="high_quality",  # Use high quality settings
            buffer=128
        ),
        cache_enabled=True,
        verbose=True
    )
    
    print(f"📍 Target area: {config.bbox.to_string()}")
    print(f"🎯 Feature types: {[f.value for f in config.features.types]}")
    print(f"🔍 Zoom levels: {config.tiles.min_zoom}-{config.tiles.max_zoom}")
    print(f"⚙️  Quality profile: {config.tiles.quality_profile}")
    
    # 2. Initialize components
    cache_manager = CacheManager(config.output.cache_dir, enabled=config.cache_enabled)
    tile_generator = TileGenerator(config, cache_manager)
    
    # 3. Check tippecanoe availability
    print("\n🔧 System Check:")
    if tile_generator.validate_tippecanoe():
        print("✅ tippecanoe is available and ready")
    else:
        print("❌ tippecanoe not found. Please install tippecanoe:")
        print("   brew install tippecanoe")
        return 1
    
    # 4. Get processing information
    info = tile_generator.get_processing_info()
    print(f"💾 Available memory: {info['system']['available_memory_gb']} GB")
    print(f"🖥️  CPU cores: {info['system']['cpu_count']}")
    
    # 5. Create sample GeoJSON files for demonstration
    print("\n📁 Creating sample GeoJSON files...")
    sample_files = create_sample_geojson_files(config.output.data_dir)
    
    if not sample_files:
        print("❌ No sample files created. In a real scenario, you would:")
        print("   1. Download OSM data for the bounding box")
        print("   2. Extract features using FeatureExtractor")
        print("   3. Pass the extracted GeoJSON files to TileGenerator")
        return 1
    
    # 6. Generate tiles with comprehensive error handling
    print(f"\n🏗️  Generating vector tiles from {len(sample_files)} feature files...")
    
    try:
        # Generate tiles
        output_path = tile_generator.generate(sample_files)
        
        print(f"✅ Tiles generated successfully: {output_path}")
        
        # 7. Get detailed information about generated tiles
        tile_info = tile_generator.get_tile_info(output_path)
        
        print("\n📊 Tile Generation Results:")
        print(f"   📦 Total tiles: {tile_info['tile_count']:,}")
        print(f"   🔍 Zoom range: {tile_info['zoom_range']['min']}-{tile_info['zoom_range']['max']}")
        print(f"   📏 File size: {tile_info['file_info']['size_bytes']:,} bytes")
        print(f"   📈 Average tile size: {tile_info['tile_sizes']['average_bytes']} bytes")
        
        # Show tiles per zoom level
        print("   📋 Tiles per zoom level:")
        for zoom, count in tile_info['tiles_per_zoom'].items():
            print(f"      Zoom {zoom}: {count:,} tiles")
        
        # Processing statistics
        if 'processing_stats' in tile_info:
            stats = tile_info['processing_stats']
            print(f"   ⏱️  Processing time: {stats.get('duration', 'N/A')}")
            print(f"   💾 Peak memory: {stats.get('memory_peak_mb', 0):.1f}%")
            if stats.get('retries', 0) > 0:
                print(f"   🔄 Retries: {stats['retries']}")
        
        print(f"\n🎉 Success! Vector tiles are ready at: {output_path}")
        print("You can now use these tiles with MapLibre GL JS or other vector tile renderers.")
        
        return 0
        
    except Exception as e:
        print(f"❌ Tile generation failed: {e}")
        print("\n🔧 Troubleshooting tips:")
        print("   • Ensure tippecanoe is installed and in PATH")
        print("   • Check that input GeoJSON files are valid")
        print("   • Verify sufficient disk space and memory")
        print("   • Try a smaller bounding box or lower quality profile")
        return 1
    
    finally:
        # Cleanup
        tile_generator.cleanup_temp_files()


def create_sample_geojson_files(data_dir: Path) -> dict:
    """Create sample GeoJSON files for demonstration."""
    import json
    
    data_dir.mkdir(parents=True, exist_ok=True)
    files = {}
    
    # Sample river data
    rivers_data = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[-105.015, 39.742], [-105.012, 39.748]]
                },
                "properties": {
                    "waterway": "river",
                    "name": "Boulder Creek"
                }
            }
        ]
    }
    
    rivers_path = data_dir / "rivers.geojson"
    with open(rivers_path, 'w') as f:
        json.dump(rivers_data, f)
    files["rivers"] = rivers_path
    
    # Sample road data
    roads_data = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[-105.018, 39.740], [-105.014, 39.745], [-105.010, 39.750]]
                },
                "properties": {
                    "highway": "primary",
                    "name": "Broadway"
                }
            }
        ]
    }
    
    roads_path = data_dir / "roads.geojson"
    with open(roads_path, 'w') as f:
        json.dump(roads_data, f)
    files["roads"] = roads_path
    
    # Sample building data
    buildings_data = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[-105.016, 39.744], [-105.015, 39.744], [-105.015, 39.745], [-105.016, 39.745], [-105.016, 39.744]]]
                },
                "properties": {
                    "building": "yes",
                    "name": "Sample Building"
                }
            }
        ]
    }
    
    buildings_path = data_dir / "buildings.geojson"
    with open(buildings_path, 'w') as f:
        json.dump(buildings_data, f)
    files["buildings"] = buildings_path
    
    print(f"✅ Created {len(files)} sample GeoJSON files")
    return files


if __name__ == "__main__":
    exit(main()) 