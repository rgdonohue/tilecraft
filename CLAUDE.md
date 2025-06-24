# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Tilecraft is an AI-assisted CLI tool for generating vector tiles from OpenStreetMap (OSM) data. It uses AI to generate schemas and styles, processes OSM data through a pipeline of feature extraction and tile generation, and outputs MapLibre-compatible vector tiles and styles.

## Development Commands

### Testing
```bash
# Run all tests with coverage
pytest

# Run specific test types  
pytest -m unit
pytest -m integration
pytest -m "not slow"

# Run tests for specific component
pytest tests/test_feature_extractor.py
pytest tests/test_tile_generator.py::test_specific_function
```

### Code Quality
```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Type checking
mypy src/

# Run all quality checks
black src/ tests/ && ruff check src/ tests/ && mypy src/
```

### Installation & Setup
```bash
# Install development dependencies
pip install -e .[dev]

# Install test dependencies only
pip install -e .[test]

# Install all optional dependencies
pip install -e .[dev,test,docs]
```

### Running the CLI
```bash
# Basic usage
tilecraft --bbox "-109.2,36.8,-106.8,38.5" --features "rivers,forest,water" --palette "subalpine dusk"

# With additional options
tilecraft --bbox "-120.5,35.0,-120.0,35.5" --features "rivers,forest,water" --palette "pacific northwest" --name "big_sur" --max-zoom 16 --verbose
```

## Architecture

### Core Pipeline (src/tilecraft/core/)
The main processing pipeline orchestrates:
1. **OSM Downloader** (`osm_downloader.py`) - Downloads OSM data for bounding box
2. **Feature Extractor** (`feature_extractor.py`) - Extracts specific features (roads, buildings, water, etc.) from OSM data 
3. **Tile Generator** (`tile_generator.py`) - Uses tippecanoe to generate vector tiles from extracted features
4. **Pipeline** (`pipeline.py`) - Orchestrates the complete workflow

### AI Integration (src/tilecraft/ai/)
- **Schema Generator** (`schema_generator.py`) - Uses AI to generate optimal tile schemas based on requested features
- **Style Generator** (`style_generator.py`) - Generates MapLibre GL JS styles based on palette and geographic context
- **Tag Disambiguator** (`tag_disambiguator.py`) - Handles OSM tag variations and regional differences

### Configuration (src/tilecraft/models/)
- **Config models** (`config.py`) - Pydantic models for configuration validation
- **Schemas** (`schemas.py`) - Data models for tile schemas

### System Requirements
- **External tools**: osmium-tool, tippecanoe, gdal (must be installed via brew/apt/conda)
- **Python 3.9+** with geospatial libraries (GDAL, Shapely, Fiona)
- **AI API keys**: OpenAI or Anthropic for schema/style generation

### Key Data Flow
1. CLI validates inputs and creates TilecraftConfig
2. Pipeline downloads OSM data for bbox and caches it
3. Feature extractor processes OSM → GeoJSON for each feature type
4. AI generates tile schema based on requested features
5. Tippecanoe generates .mbtiles from GeoJSON files
6. AI generates MapLibre style JSON from schema and palette

### Output Structure
```
output/
├── tiles/          # .mbtiles vector tiles
├── styles/         # MapLibre GL JS style JSON
├── data/           # Extracted GeoJSON files + schema.json
└── cache/          # Cached OSM data
```

### Feature Types
Supported features: rivers, forest, water, lakes, parks, roads, buildings
Each maps to specific OSM tags and geometry types defined in the feature extractor.

### Testing Strategy
- Unit tests for individual components
- Integration tests for pipeline workflow  
- Fixtures in tests/fixtures/ for test data
- Coverage reporting via pytest-cov