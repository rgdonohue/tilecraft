# Vector Tile Schema Generation Prompts

## Core Schema Prompt

```markdown
Generate a comprehensive vector tile schema for the following OSM feature types: {feature_types}

Requirements:
- Include geometry type (Point, LineString, Polygon)
- Specify recommended zoom levels (minzoom/maxzoom)
- Define essential attributes for each feature type
- Consider memory efficiency and tile size constraints
- Follow Mapbox Vector Tile specification v2.1

For each feature type, provide:
1. Primary OSM tags to include
2. Secondary/optional attributes
3. Recommended attribute data types
4. Zoom level optimization strategy
5. Attribute filtering rules by zoom level

Output format: JSON schema with layer definitions
```

## Feature-Specific Prompts

### Rivers & Waterways
```markdown
Context: Generating schema for water features from OSM data
Feature types: rivers, streams, canals, waterways

OSM Tags to consider:
- waterway=* (river, stream, canal, drain)
- name=* (waterway names)
- width=* (waterway width)
- tunnel=* (underground waterways)
- bridge=* (elevated waterways)

Zoom strategy:
- Major rivers: zoom 6+
- Minor streams: zoom 12+
- Attribute detail: increase with zoom level
```

### Forest & Vegetation
```markdown
Context: Generating schema for forest/vegetation from OSM data
Feature types: forests, woods, nature reserves

OSM Tags to consider:
- landuse=forest
- natural=wood
- leisure=nature_reserve
- leaf_type=* (deciduous, coniferous, mixed)
- name=* (forest/park names)

Handle tag disambiguation:
- landuse=forest vs natural=wood (same feature type)
- Include both tags for comprehensive coverage
```

### Water Bodies
```markdown
Context: Generating schema for water bodies from OSM data
Feature types: lakes, ponds, reservoirs

OSM Tags to consider:
- natural=water
- landuse=reservoir
- water=* (lake, pond, reservoir)
- name=* (water body names)

Zoom strategy:
- Large lakes: zoom 6+
- Small ponds: zoom 14+
```

## Schema Validation Prompt

```markdown
Validate this vector tile schema for geospatial correctness:
{schema_json}

Check for:
1. Geometry type compatibility with feature types
2. Zoom level logic (minzoom <= maxzoom)
3. Attribute data type consistency
4. Missing essential attributes for cartographic rendering
5. Memory efficiency considerations
6. Mapbox Vector Tile spec compliance

Suggest improvements for:
- Performance optimization
- Cartographic best practices
- Accessibility considerations
```

## Error Handling Prompt

```markdown
The schema generation failed with error: {error_message}

Context: OSM feature types: {feature_types}
Bounding box: {bbox}

Provide:
1. Likely cause of the error
2. Fallback schema recommendation
3. Debugging steps
4. Alternative approach if needed

Generate a minimal working schema as fallback.
``` 