# 📚 Tilecraft Documentation

Welcome to the Tilecraft documentation! This guide helps you find the right information for your needs.

## 🚀 Getting Started

### For New Users
- **[Main README](../README.md)** - Complete overview, installation, and usage guide
- **[Product Requirements Document](PRD.md)** - Detailed project specifications and goals
- **[Project Status](PROJECT_STATUS.md)** - Current development progress and roadmap

### For Developers
- **[Project Structure](project_structure.md)** - Codebase organization and architecture
- **[Development Setup](../README.md#development)** - Environment setup and contribution guidelines

## 🗺️ Testing & Validation

### GIS Testing
- **[QGIS Testing Guide](QGIS_TESTING_GUIDE.md)** - How to test vector tiles in QGIS and other GIS applications
  - Real output analysis and validation
  - Performance metrics and expected results
  - Alternative testing tools (MapLibre, TileServer)

## 🚨 Troubleshooting

### Common Issues
- **[Troubleshooting Guide](../README.md#troubleshooting)** - Complete troubleshooting section in main README
  - System dependency issues
  - Performance problems
  - Error resolution
  - Debug mode instructions

### System Requirements
- **Dependencies**: `tilecraft check --verbose`
- **Installation Help**: `tilecraft check --fix`
- **Platform-specific**: See main README installation section

## 📁 Documentation Structure

```
docs/
├── README.md                    # This file - documentation index
├── PRD.md                      # Product Requirements Document
├── PROJECT_STATUS.md           # Current project status and roadmap
├── project_structure.md        # Codebase architecture
├── QGIS_TESTING_GUIDE.md       # GIS testing and validation
└── archives/                   # Historical and development documents
    ├── AGENTIC_DEVELOPMENT_LEARNINGS_REPORT.md
    ├── AGENTIC_SETUP.md
    ├── CLAUDE.md
    ├── ENHANCED_AGENTIC_WORKFLOW.md
    ├── IMMEDIATE_ACTIONS.md
    ├── mcp-config.md
    ├── REAL_OUTPUT_ANALYSIS.md
    ├── RECOMMENDED_NEXT_STEPS.md
    └── tech-decision.md
```

## 🔍 Quick Reference

### Essential Commands
```bash
# Check system dependencies
tilecraft check --verbose

# Basic usage
tilecraft --bbox "west,south,east,north" --features "rivers,forest" --palette "subalpine dusk"

# With options
tilecraft --bbox "-109.2,36.8,-106.8,38.5" \
  --features "rivers,forest,water" \
  --palette "subalpine dusk" \
  --max-zoom 14 \
  --output my_project \
  --verbose
```

### Supported Features
- **Natural**: `rivers`, `forest`, `water`, `lakes`, `wetlands`
- **Urban**: `roads`, `buildings`, `parks`
- **Custom**: Extensible via configuration

### Style Palettes
- `subalpine dusk` - Muted mountain colors
- `desert sunset` - Warm earth tones
- `pacific northwest` - Deep greens and blues
- `urban midnight` - High contrast city theme
- `arctic` - Cool blues and whites
- `tropical` - Vibrant greens and blues

## 🤝 Contributing

1. **Read the main README** for development setup
2. **Check project status** for current priorities
3. **Review project structure** for codebase organization
4. **Follow testing guidelines** for validation

## 📞 Support

- **Issues**: Create GitHub issue for bugs or feature requests
- **Discussions**: Use GitHub Discussions for questions
- **Documentation**: Check this guide and main README first
- **System Check**: Run `tilecraft check --fix` for installation help

---

*Need help? Start with the [main README](../README.md) and [troubleshooting section](../README.md#troubleshooting).* 