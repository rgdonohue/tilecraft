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
- 🗂️ **50+ Feature Types**: Comprehensive OSM feature support across 9 categories

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
```

### Basic Usage

```bash
# Generate tiles for Colorado rivers and forests
tilecraft generate \
  --bbox "-109.2,36.8,-106.8,38.5" \
  --features "rivers,forest,water" \
  --palette "subalpine dusk" \
  --name "colorado_nature"

# Quick urban mapping
tilecraft generate \
  --bbox "-122.5,37.7,-122.3,37.8" \
  --features "roads,buildings,parks,restaurants" \
  --palette "urban midnight" \
  --name "san_francisco"

# Comprehensive regional mapping
tilecraft generate \
  --bbox "-105.5,39.5,-105.0,40.0" \
  --features "rivers,lakes,mountains,forest,roads,buildings" \
  --palette "alpine blue" \
  --name "colorado_comprehensive"
```

## 📖 CLI Commands

### Main Commands

**Generate Vector Tiles**
```bash
tilecraft generate [OPTIONS]

Required:
  --bbox TEXT        Bounding box as 'west,south,east,north'
  --features TEXT    Comma-separated feature types (see 'tilecraft features')
  --palette TEXT     Style palette mood (e.g., 'subalpine dusk')

Optional:
  --output PATH      Output directory (default: output)
  --name TEXT        Project name for file naming
  --min-zoom INT     Minimum zoom level (default: 0)
  --max-zoom INT     Maximum zoom level (default: 14)
  --no-cache         Disable caching
  --preview          Generate preview after tile creation
  --verbose, -v      Verbose output
  --quiet, -q        Quiet mode
```

**Explore Available Features**
```bash
tilecraft features [OPTIONS]

Options:
  --category TEXT    Filter by category (water, natural, transportation, etc.)
  --search TEXT      Search feature names and descriptions
  --count INT        Number of features to show (default: 50)
```

**Check System Dependencies**
```bash
tilecraft check [OPTIONS]

Options:
  --verbose, -v      Show detailed dependency information
  --fix              Show installation commands for missing dependencies
```

### Usage Examples

**Discover Features**
```bash
# See all 50+ available features
tilecraft features

# Find water-related features
tilecraft features --search "water"

# See transportation options
tilecraft features --category "transportation"

# Explore natural features
tilecraft features --category "natural"
```

**Natural Features Mapping**
```bash
tilecraft generate \
  --bbox "-120.5,35.0,-120.0,35.5" \
  --features "rivers,forest,water,wetlands,mountains,beaches" \
  --palette "pacific northwest" \
  --name "big_sur_nature"
```

**Urban Planning Analysis**
```bash
tilecraft generate \
  --bbox "-74.1,40.6,-73.9,40.8" \
  --features "roads,buildings,parks,schools,hospitals,restaurants" \
  --palette "metropolitan" \
  --max-zoom 16 \
  --name "manhattan_urban"
```

**Infrastructure Mapping**
```bash
tilecraft generate \
  --bbox "-118.5,34.0,-118.0,34.5" \
  --features "roads,railways,airports,power_lines,bridges" \
  --palette "industrial" \
  --name "la_infrastructure"
```

**Recreational Planning**
```bash
tilecraft generate \
  --bbox "-106.0,39.0,-105.5,39.5" \
  --features "parks,playgrounds,sports_fields,golf_courses,mountains,rivers" \
  --palette "recreational" \
  --name "denver_recreation"
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
│   ├── buildings.geojson
│   ├── roads.geojson
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
# Processing Configuration
TILECRAFT_CACHE_ENABLED=true
```

### Supported Features

**🗺️ 52 Feature Types Available Across 8 Categories:**

- **Water Features (6)**: rivers, water, lakes, wetlands, waterways, coastline
- **Natural Features (8)**: forest, woods, mountains, peaks, cliffs, beaches, glaciers, volcanoes  
- **Land Use (7)**: parks, farmland, residential, commercial, industrial, military, cemeteries
- **Transportation (8)**: roads, highways, railways, airports, bridges, tunnels, paths, cycleways
- **Built Environment (5)**: buildings, churches, schools, hospitals, universities
- **Amenities (6)**: restaurants, shops, hotels, banks, fuel_stations, post_offices
- **Recreation (5)**: playgrounds, sports_fields, golf_courses, stadiums, swimming_pools
- **Infrastructure (5)**: power_lines, wind_turbines, solar_farms, dams, barriers
- **Administrative (2)**: boundaries, protected_areas

**✨ All Features Fully Supported with:**
- Optimized OSM Overpass queries
- Smart tag extraction and filtering  
- Automatic geometry validation
- Efficient caching and processing

To see all available features:
```bash
# List all features by category
tilecraft features

# Search for specific features
tilecraft features --search "water"

# Filter by category
tilecraft features --category "transportation"
```

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
5. **Graceful Resource Management**: Proper cleanup prevents hanging and ensures smooth operation

## 🚨 Troubleshooting

### Quick System Check

```bash
# Check all dependencies and get installation help
tilecraft check --verbose --fix
```

### Common Issues

#### ❌ "tilecraft command not found"
**Solution:** Install tilecraft in development mode
```bash
# Make sure you're in the tilecraft directory and virtual environment is active
source .venv/bin/activate
pip install -e .
```

#### ❌ "No such option: --bbox"
**Solution:** Use the `generate` subcommand
```bash
# ❌ Wrong - missing 'generate'
tilecraft --bbox "..." --features "..." --palette "..."

# ✅ Correct - include 'generate' subcommand
tilecraft generate --bbox "..." --features "..." --palette "..."
```

#### ❌ "tippecanoe not found"
**Solutions:**
```bash
# macOS
brew install tippecanoe

# Ubuntu/Debian  
sudo apt-get install tippecanoe

# Check installation
tippecanoe --version
```

#### ❌ "CLI hangs after tile generation"
**Solution:** This has been fixed! The CLI now properly cleans up resources and exits gracefully.

#### ❌ "Invalid bounding box format"
**Solution:** Use correct format: `west,south,east,north`
```bash
# ✅ Correct format
tilecraft generate --bbox "-109.2,36.8,-106.8,38.5" --features "rivers" --palette "subalpine dusk"

# ❌ Common mistakes:
# Missing quotes, wrong order, extra spaces
```

#### ❌ "Unknown feature type"
**Solution:** Check available features
```bash
# See all available features
tilecraft features

# Search for specific features
tilecraft features --search "water"

# Check spelling - feature names are case-sensitive
```

### Performance Tips

- **Large regions:** Use `--max-zoom 12` instead of 14
- **Memory issues:** Process smaller bounding boxes
- **Slow processing:** Close other applications, use SSD storage
- **Cache:** Use `--no-cache` if running low on disk space

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
- [Tippecanoe](https://github.com/felt/tippecanoe) by Mapbox
- [Osmium](https://osmcode.org/osmium-tool/) by OSM developers
- [MapLibre GL JS](https://maplibre.org/) community

## 📞 Support

- 🔧 **System Check**: `tilecraft check --fix` for installation help
- 🗺️ **Feature Discovery**: `tilecraft features` to explore options
- 🐛 **Issues**: Check existing issues or create new one
- 💬 **Discussions**: Community support and questions

---

*"The best way to find out if you can trust somebody is to trust them." – Ernest Hemingway*