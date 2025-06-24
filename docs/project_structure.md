# Recommended Project Structure

```
tilecraft/
├── src/
│   └── tilecraft/
│       ├── __init__.py
│       ├── cli.py                    # Main CLI entry point
│       ├── core/
│       │   ├── __init__.py
│       │   ├── bbox.py              # Bounding box validation
│       │   ├── osm_downloader.py    # OSM data acquisition
│       │   ├── feature_extractor.py # OSM feature filtering
│       │   └── tile_generator.py    # Tippecanoe integration
│       ├── ai/
│       │   ├── __init__.py
│       │   ├── schema_generator.py  # AI schema generation
│       │   ├── style_generator.py   # AI style generation  
│       │   ├── tag_disambiguator.py # AI tag matching
│       │   └── prompts.py          # Prompt templates
│       ├── models/
│       │   ├── __init__.py
│       │   ├── config.py           # Pydantic models
│       │   └── schemas.py          # Tile schema definitions
│       └── utils/
│           ├── __init__.py
│           ├── cache.py            # Caching utilities
│           ├── validation.py       # Data validation
│           └── preview.py          # Preview generation
├── tests/
│   ├── __init__.py
│   ├── conftest.py                 # Pytest configuration
│   ├── test_cli.py
│   ├── test_osm_processing.py
│   ├── test_ai_integration.py
│   └── fixtures/                   # Test data
│       ├── sample.osm.pbf
│       └── expected_outputs/
├── prompts/                        # AI prompt library
│   ├── schema_generation.md
│   ├── style_generation.md
│   ├── tag_disambiguation.md
│   └── code_review.md
├── docs/                          # Documentation
│   ├── api.md
│   ├── examples.md
│   └── troubleshooting.md
├── scripts/                       # Development scripts
│   ├── setup_dev_env.sh
│   ├── install_system_deps.sh
│   └── run_tests.sh
├── examples/                      # Usage examples
│   ├── colorado_rivers.sh
│   └── forest_mapping.sh
├── .cursor/                       # Cursor configuration
│   └── settings.json
├── .env.example                   # Environment variables template
├── pyproject.toml                 # Python project configuration
├── README.md                      # Project README
├── CONTRIBUTING.md               # Development guidelines
└── .gitignore                    # Git ignore patterns
```

## Key Design Principles

### 1. **Separation of Concerns**
- `core/`: Pure GIS/OSM logic, no AI dependencies
- `ai/`: AI integration layer, swappable providers
- `models/`: Data structures and validation
- `utils/`: Cross-cutting utilities

### 2. **Testability**
- Clear interfaces between modules
- Dependency injection for external services
- Comprehensive fixture data for testing

### 3. **Configurability**
- Environment-based configuration
- Pydantic models for type safety
- Clear separation of user config vs system config

### 4. **Extensibility**
- Plugin architecture for new feature types
- Multiple AI provider support
- Customizable output formats

## Development Priority Order

1. **Core CLI** (`cli.py`) - Basic argument parsing
2. **Data Models** (`models/`) - Type definitions
3. **OSM Processing** (`core/`) - Data pipeline
4. **AI Integration** (`ai/`) - Schema & style generation
5. **Testing** (`tests/`) - Comprehensive coverage
6. **Documentation** (`docs/`) - User guides 