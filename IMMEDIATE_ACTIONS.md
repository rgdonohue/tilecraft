# 🚀 Immediate Action Plan (Next 2-3 Hours)

## Priority 1: Foundation Setup (30 mins)

### 1.1 System Dependencies
```bash
# Install system dependencies (macOS)
brew install osmium-tool tippecanoe gdal

# Verify installations
osmium --version
tippecanoe --version
gdalinfo --version
```

### 1.2 Python Environment
```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install Poetry (recommended)
pip install poetry
```

### 1.3 Project Bootstrap
**Cursor Composer Command:**
```
Generate a complete Python CLI project structure for tilecraft with:
- pyproject.toml with geospatial dependencies
- src/tilecraft/ package structure
- Click-based CLI entry point
- Pydantic models for configuration
- Basic test structure with pytest
```

## Priority 2: Core CLI (45 mins)

### 2.1 Basic CLI Structure
**Cursor Composer Command:**
```
Create a Click-based CLI in src/tilecraft/cli.py that accepts:
- --bbox: bounding box as "west,south,east,north"  
- --features: comma-separated list (rivers,forest,water)
- --palette: style mood string (e.g., "subalpine dusk")
- --output: output directory path
Include rich console output for beautiful CLI experience
```

### 2.2 Configuration Models
**Cursor Composer Command:**
```
Create Pydantic models in src/tilecraft/models/config.py for:
- BoundingBox (with validation)
- FeatureConfig (supported feature types)
- PaletteConfig (style configuration)
- OutputConfig (file paths and options)
```

## Priority 3: AI Integration Foundation (60 mins)

### 3.1 AI Client Setup
**Cursor Composer Command:**
```
Create src/tilecraft/ai/client.py with:
- OpenAI and Anthropic client configuration
- Environment variable handling
- Retry logic and error handling
- Token usage tracking
```

### 3.2 Prompt Templates
**Cursor Composer Command:**
```
Create comprehensive prompt templates in src/tilecraft/ai/prompts.py:
- Schema generation prompt with OSM feature context
- MapLibre style generation with palette support
- OSM tag disambiguation for fuzzy matching
- Error handling and validation prompts
```

## Priority 4: First Working Prototype (45 mins)

### 4.1 OSM Data Pipeline Stub
**Cursor Composer Command:**
```
Create src/tilecraft/core/osm_downloader.py with:
- Bounding box to Overpass API query
- Basic OSM data download with caching
- File validation and error handling
- Progress indication with rich progress bars
```

### 4.2 Integration Test
**Cursor Composer Command:**
```
Create a working end-to-end test that:
1. Takes a small bounding box (e.g., downtown area)
2. Downloads OSM data
3. Calls AI for schema generation
4. Outputs structured results
5. Validates all file outputs exist
```

## Priority 5: Development Workflow (30 mins)

### 5.1 Cursor Configuration
```bash
mkdir -p .cursor
cat > .cursor/settings.json << 'EOF'
{
  "cursor.ai.model": "claude-3.5-sonnet",
  "cursor.ai.enableCodeCompletion": true,
  "cursor.ai.enableInlineCompletion": true,
  "cursor.chat.contextLength": 16000,
  "cursor.chat.systemPrompt": "You are a GIS and geospatial expert helping develop an OSM vector tile CLI tool. Focus on robust error handling, performance optimization, and following geospatial best practices."
}
EOF
```

### 5.2 Environment Setup
```bash
# Copy environment template
cp .env.example .env

# Add your API keys
echo "OPENAI_API_KEY=your_key_here" >> .env
echo "ANTHROPIC_API_KEY=your_key_here" >> .env
```

## 🎯 Success Criteria (End of Session)

- [ ] **Runnable CLI**: `tilecraft --help` works
- [ ] **Basic Pipeline**: Can download OSM data for a small bbox
- [ ] **AI Integration**: Can generate a schema via AI
- [ ] **File Output**: Creates proper directory structure
- [ ] **Testing**: Has at least one integration test passing
- [ ] **Development Ready**: Full agentic workflow established

## 🚀 Next Development Commands

After completing setup, use these Cursor Composer commands:

```bash
# Implement feature extraction
"Create OSM feature extractor that filters rivers, forests, and water bodies from OSM data using osmium"

# Add tippecanoe integration  
"Create tile generator that converts GeoJSON to MBTiles using tippecanoe with zoom-appropriate settings"

# Implement AI style generation
"Create MapLibre style generator that produces beautiful styles based on palette mood and feature types"

# Add comprehensive error handling
"Add robust error handling throughout the pipeline with user-friendly error messages"
```

## 💡 Pro Tips

1. **Start Small**: Test with tiny bounding boxes first (single city block)
2. **Cache Everything**: Implement caching from day 1 for fast iteration
3. **AI-First**: Generate code structure first, then optimize
4. **Test-Driven**: Write failing tests, then implement features
5. **Rich Output**: Use rich library for beautiful CLI feedback 