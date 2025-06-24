# Custom MCP Configuration for Geospatial Development

## 🗺️ Geospatial-Specific MCP Setup

### 1. OSM Tag Reference MCP
```json
{
  "name": "osm-tags",
  "description": "Provides comprehensive OSM tag documentation and usage patterns",
  "endpoints": {
    "tag_lookup": "https://taginfo.openstreetmap.org/api/4/tag/stats",
    "feature_mapping": "./config/osm_feature_mappings.json"
  },
  "context_files": [
    "docs/osm_tag_reference.md",
    "config/supported_features.yaml"
  ]
}
```

### 2. MapLibre Style Reference MCP
```json
{
  "name": "maplibre-styles", 
  "description": "MapLibre GL JS style specification and examples",
  "context_files": [
    "docs/maplibre_style_spec.json",
    "examples/style_templates/",
    "config/color_palettes.yaml"
  ]
}
```

### 3. Geospatial Best Practices MCP
```json
{
  "name": "gis-practices",
  "description": "GIS processing patterns and geospatial data handling",
  "context_files": [
    "docs/projection_handling.md",
    "docs/geometry_validation.md", 
    "docs/performance_optimization.md"
  ]
}
```

## 🚀 Implementation Strategy

### Step 1: Create Context Files
```bash
mkdir -p config docs examples/style_templates

# OSM feature mapping
cat > config/osm_feature_mappings.json << 'EOF'
{
  "water": {
    "natural": ["water", "bay", "strait"],
    "waterway": ["river", "stream", "canal", "drain"],
    "landuse": ["reservoir", "basin"]
  },
  "forest": {
    "natural": ["wood", "forest", "scrub"],
    "landuse": ["forest", "orchard"],
    "leisure": ["nature_reserve", "park"]
  },
  "rivers": {
    "waterway": ["river", "stream", "canal", "ditch"],
    "natural": ["water"],
    "water": ["river", "stream"]
  }
}
EOF

# Color palettes
cat > config/color_palettes.yaml << 'EOF'
palettes:
  subalpine_dusk:
    water: "#4A90E2"
    rivers: "#00D4FF" 
    forest: "#2E8B57"
    background: "#2C3E50"
  desert_sunset:
    water: "#1E88E5"
    rivers: "#42A5F5"
    forest: "#8BC34A"
    background: "#FFA726"
EOF
```

### Step 2: Cursor MCP Integration
Add to `.cursor/settings.json`:
```json
{
  "cursor.mcp.servers": {
    "osm-context": {
      "command": "npx",
      "args": ["@cursor/mcp-server-filesystem", "./config"],
      "env": {
        "MCP_SERVER_NAME": "osm-context"
      }
    }
  }
}
```

## 🤖 AI-Enhanced Development Patterns

### Pattern 1: Context-Aware Feature Development
```bash
# Before implementing feature extraction:
@cursor "Using the OSM tag mappings in config/, implement feature extraction for rivers that handles all waterway variants and edge cases"
```

### Pattern 2: Style Generation with Palette Context
```bash  
# Before generating styles:
@cursor "Using the color palettes in config/color_palettes.yaml, generate a MapLibre style for the 'subalpine_dusk' theme with proper contrast ratios"
```

### Pattern 3: GIS-Aware Error Handling
```bash
# Before implementing validation:
@cursor "Using geospatial best practices, add comprehensive geometry validation that handles common OSM data issues like self-intersecting polygons"
```

## 📚 Reference Documentation to Include

### 1. OSM Tag Reference (`docs/osm_tag_reference.md`)
- Complete tag taxonomy for natural features
- Regional variations and common misspellings
- Tag frequency statistics from taginfo
- Conflicting tag resolution strategies

### 2. MapLibre Style Specification (`docs/maplibre_style_spec.json`)
- Complete style specification JSON
- Layer type examples
- Paint property references
- Expression syntax guide

### 3. Performance Guidelines (`docs/performance_optimization.md`)
- Memory management for large bounding boxes
- Streaming strategies for OSM data
- Tippecanoe optimization parameters
- Caching strategies

## 🔧 Advanced MCP Features

### Dynamic Context Loading
```python
# In your AI client:
async def load_osm_context(feature_types: List[str]) -> str:
    """Load relevant OSM context based on requested features"""
    context = []
    for feature in feature_types:
        if feature in OSM_MAPPINGS:
            context.append(f"Feature {feature}: {OSM_MAPPINGS[feature]}")
    return "\n".join(context)
```

### Style Template Injection
```python
async def get_style_template(palette: str) -> Dict:
    """Get style template with palette-specific colors"""
    base_template = load_template("base_style.json")
    palette_colors = load_palette(palette)
    return merge_template_colors(base_template, palette_colors)
```

## 🎯 Expected Benefits

1. **Faster Development**: AI has immediate access to geospatial context
2. **Fewer Errors**: AI understands OSM tag complexities upfront  
3. **Consistent Patterns**: AI follows established GIS best practices
4. **Better Code Quality**: AI suggests optimizations based on geospatial knowledge

## 🚀 Quick Setup Commands

```bash
# Create all MCP context files
@cursor "Generate comprehensive OSM tag documentation and MapLibre style templates based on the tilecraft feature requirements"

# Test MCP integration
@cursor "Using the MCP context, explain the difference between natural=water and waterway=river tags in OSM"

# Validate setup
@cursor "Generate a sample MapLibre style using the subalpine_dusk palette from MCP context"
``` 