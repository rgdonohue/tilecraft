# Agentic Development Environment Setup

## 🤖 AI-First Development Strategy

### Cursor Configuration
```json
// .cursor/settings.json
{
  "cursor.ai.model": "claude-3.5-sonnet",
  "cursor.ai.enableCodeCompletion": true,
  "cursor.ai.enableInlineCompletion": true,
  "cursor.chat.contextLength": 16000
}
```

### Key Agentic Workflows

#### 1. **AI Prompt Library** (Immediate Setup)
Create `prompts/` directory with:
- `schema_generation.md` - Vector tile schema prompts
- `style_generation.md` - MapLibre style prompts  
- `tag_disambiguation.md` - OSM tag matching prompts
- `code_review.md` - Code quality & GIS best practices

#### 2. **Test-Driven Agentic Development**
```bash
# Create test cases FIRST, then ask AI to implement
tests/
├── test_bounding_box.py
├── test_osm_extraction.py
├── test_ai_schema_gen.py
└── test_style_generation.py
```

#### 3. **AI-Assisted Architecture**
- Use Cursor to generate initial project structure
- AI-driven API design for clean separation of concerns
- Automated refactoring suggestions

## 🛠️ Development Tools Integration

### MCP (Model Context Protocol) Opportunities
1. **Custom OSM MCP**: Direct osmium-tool integration
2. **Tippecanoe MCP**: Vector tile generation context
3. **MapLibre MCP**: Style validation & rendering
4. **GIS Validation MCP**: Geometry & projection checks

### Cursor Composer Usage
- **Feature Implementation**: "Implement OSM data download with caching"
- **Bug Fixing**: "Fix geometry validation errors in GeoJSON export"
- **Optimization**: "Optimize memory usage for large bounding boxes"
- **Documentation**: "Generate API docs from code comments"

## 🔄 Agentic Workflow Patterns

### Pattern 1: AI-First Feature Development
1. **Prompt Engineering**: Define feature requirements in natural language
2. **AI Implementation**: Generate initial code structure
3. **Human Review**: Validate GIS logic and edge cases  
4. **AI Refinement**: Iterate based on feedback
5. **Test Generation**: AI creates comprehensive test cases

### Pattern 2: Continuous AI Assistance
- **Code Review**: AI suggests improvements during development
- **Documentation**: Auto-generate docstrings and README updates
- **Error Handling**: AI suggests robust error handling patterns
- **Performance**: AI identifies bottlenecks and optimization opportunities

### Pattern 3: Domain-Specific AI Context
- Load OSM tag documentation into context
- Include MapLibre style specification
- Provide tippecanoe parameter reference
- Maintain geospatial best practices knowledge

## 🚀 Quick Start Commands

```bash
# 1. Setup project structure (AI-generated)
@cursor "Generate a Python CLI project structure for tilecraft"

# 2. Bootstrap dependencies
@cursor "Create pyproject.toml with geospatial dependencies"

# 3. Implement core CLI
@cursor "Create Click-based CLI with bbox, features, palette args"

# 4. Add AI integration
@cursor "Add OpenAI/Anthropic client for schema generation"
```

## 📊 Success Metrics
- **Development Speed**: Target 2-3x faster than traditional development
- **Code Quality**: AI-suggested improvements reduce bugs by 40%
- **Documentation**: 90% auto-generated, always up-to-date
- **Testing**: Comprehensive test coverage through AI generation 