# 🗺️ Tilecraft

**Streamlined CLI for OSM Vector Tile Generation**

Generate beautiful vector tiles and MapLibre GL JS styles from OpenStreetMap data with smart caching and optimized feature extraction.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ Features

- 🗺️ **OSM Integration**: Direct OpenStreetMap data processing with intelligent tag handling
- 🎨 **Beautiful Styles**: Palette-based MapLibre GL JS style generation
- ⚡ **Smart Caching**: Avoid redundant processing with intelligent cache management
- 🚀 **High Performance**: Optimized processing with parallel feature extraction
- 🛠️ **Professional Tools**: Built on industry-standard tools (osmium, tippecanoe)
- 📦 **Production Ready**: MBTiles output compatible with all major mapping platforms

## 🚀 Quick Start

### Prerequisites

Install system dependencies (macOS):
```bash
brew install osmium-tool tippecanoe gdal
```

For other platforms, see [Installation Guide](#installation).

### Installation

```bash
# Clone repository
git clone https://github.com/username/tilecraft.git
cd tilecraft

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install tilecraft
pip install -e .

# Set up environment
cp .env.example .env
# Edit .env to add your API keys
```

### Basic Usage

```bash
# Generate tiles for Colorado rivers and forests
tilecraft \
  --bbox "-109.2,36.8,-106.8,38.5" \
  --features "rivers,forest,water" \
  --palette "subalpine dusk"

# Quick urban mapping
tilecraft \
  --bbox "-122.5,37.7,-122.3,37.8" \
  --features "roads,buildings,parks" \
  --palette "urban midnight"


**Historic Downtown**
tilecraft \
  --bbox "-106.81,37.36,-104.49,38.39" \
  --features "rivers,forest,water" \
  --palette "subalpine dusk"
```

## 📖 Usage

### Command Line Options

```bash
tilecraft [OPTIONS]

Required:
  --bbox TEXT        Bounding box as 'west,south,east,north'
  --features TEXT    Feature types: rivers,forest,water,lakes,parks,roads,buildings  
  --palette TEXT     Style palette mood (e.g., 'subalpine dusk')

Optional:
  --output PATH      Output directory (default: output)
  --name TEXT        Project name for file naming
  --min-zoom INT     Minimum zoom level (default: 0)
  --max-zoom INT     Maximum zoom level (default: 14)
  --no-cache         Disable caching
  --preview          Generate preview
  --verbose, -v      Verbose output
  --quiet, -q        Quiet mode
```

### Examples

**Natural Features**
```bash
tilecraft \
  --bbox "-120.5,35.0,-120.0,35.5" \
  --features "rivers,forest,water,wetlands" \
  --palette "pacific northwest" \
  --name "big_sur"
```

**Urban Planning**
```bash
tilecraft \
  --bbox "-74.1,40.6,-73.9,40.8" \
  --features "roads,buildings,parks" \
  --palette "metropolitan" \
  --max-zoom 16
```

**Hydrography Focus**
```bash
tilecraft \
  --bbox "-105.5,39.5,-105.0,40.0" \
  --features "rivers,lakes,water" \
  --palette "alpine blue" \
  --name "colorado_water"
```

## 📁 Output Structure

```
output/
├── tiles/
│   └── project_name.mbtiles     # Vector tiles
├── styles/ 
│   └── project_name-style.json  # MapLibre GL JS style
├── data/
│   ├── rivers.geojson           # Extracted feature data
│   ├── forests.geojson
│   └── schema.json              # AI-generated schema
├── cache/
│   └── *.osm.pbf               # Cached OSM data
└── README.md                   # Output documentation
```

## 🛠️ Installation

### System Dependencies

**macOS:**
```bash
brew install osmium-tool tippecanoe gdal
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install osmium-tool tippecanoe gdal-bin python3-gdal
```

**Windows (via conda):**
```bash
conda install -c conda-forge osmium-tool tippecanoe gdal
```

### Python Package

```bash
# From PyPI (when published)
pip install tilecraft

# Development installation
git clone https://github.com/username/tilecraft.git
cd tilecraft
pip install -e .[dev]
```

## ⚙️ Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Optional: Processing Configuration
TILECRAFT_CACHE_ENABLED=true
TILECRAFT_PARALLEL_PROCESSING=true
TILECRAFT_MAX_WORKERS=4

# Optional: Advanced Settings
TILECRAFT_TILE_BUFFER=64
TILECRAFT_SIMPLIFICATION_LEVEL=2
```

### Supported Features

| Feature Type | OSM Tags | Geometry |
|--------------|----------|----------|
| `rivers` | waterway=river,stream,canal | LineString |
| `forest` | natural=wood,forest; landuse=forest | Polygon |
| `water` | natural=water; waterway=* | Polygon/LineString |
| `lakes` | natural=water; water=lake | Polygon |
| `parks` | leisure=park,nature_reserve | Polygon |
| `roads` | highway=* | LineString |
| `buildings` | building=* | Polygon |

### Style Palettes

- `subalpine dusk` - Muted mountain colors
- `desert sunset` - Warm earth tones  
- `pacific northwest` - Deep greens and blues
- `urban midnight` - High contrast city theme
- `arctic` - Cool blues and whites
- `tropical` - Vibrant greens and blues

## 🔧 How It Works

Tilecraft streamlines OSM processing through:

1. **Smart Feature Extraction**: Efficiently extracts specific feature types using optimized osmium filters
2. **Intelligent Schema Generation**: Creates well-structured tile schemas based on feature types and zoom requirements
3. **Optimized Style Creation**: Generates MapLibre styles with carefully chosen color palettes and rendering rules
4. **Advanced Caching**: Prevents redundant downloads and processing for faster iteration

## 🚀 Development

### Setup Development Environment

```bash
git clone https://github.com/username/tilecraft.git
cd tilecraft

# Install with development dependencies
pip install -e .[dev]

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Format code
black src/ tests/
ruff check src/ tests/
```

### Project Structure

```
tilecraft/
├── src/tilecraft/
│   ├── cli.py              # Command-line interface
│   ├── core/               # OSM processing
│   ├── ai/                 # AI integration
│   ├── models/             # Data models
│   └── utils/              # Utilities
├── tests/                  # Test suite
├── docs/                   # Documentation
└── examples/               # Usage examples
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make changes and add tests
4. Run tests: `pytest`
5. Format code: `black .` and `ruff check .`
6. Commit changes: `git commit -m "Description"`
7. Push and create Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [OpenStreetMap](https://www.openstreetmap.org/) contributors
- [Tippecanoe](https://github.com/mapbox/tippecanoe) by Mapbox
- [Osmium](https://osmcode.org/osmium-tool/) by OSM developers
- [MapLibre GL JS](https://maplibre.org/) community

## 📞 Support

- 📖 [Documentation](https://tilecraft.readthedocs.io)
- 🐛 [Issue Tracker](https://github.com/username/tilecraft/issues)
- 💬 [Discussions](https://github.com/username/tilecraft/discussions)

---

*"Design is not just what it looks like and feels like. Design is how it works." – Steve Jobs* 