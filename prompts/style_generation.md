# MapLibre Style Generation Prompts

## Core Style Prompt

```markdown
Generate a MapLibre GL JS style JSON for vector tiles with the following specifications:

Features: {feature_types}
Palette: {palette_mood}
Region: {region_description}

Requirements:
- Follow MapLibre GL JS style specification
- Ensure accessibility (WCAG AA contrast ratios)
- Use appropriate symbolization for each feature type
- Include proper source and layer definitions
- Optimize for zoom levels {min_zoom} to {max_zoom}

Style characteristics for "{palette_mood}":
- Color harmony and psychological impact
- Geographic appropriateness
- Cultural considerations for the region
- Seasonal/temporal context if relevant

Output: Complete MapLibre style JSON
```

## Palette-Specific Prompts

### Subalpine Dusk
```markdown
Create a "subalpine dusk" palette for mountain region mapping:

Colors should evoke:
- Mountain twilight atmosphere
- Cool purple/blue shadows
- Warm orange/pink highlights on peaks
- Deep forest greens
- Crystal clear water blues

Feature styling:
- Rivers: Glowing cyan (#00BFFF) with subtle outer glow
- Lakes: Deep indigo (#1E3A8A) with lighter edges
- Forests: Muted jade (#4F7942) with darker shadows
- Typography: Clean sans-serif, high contrast
- Minimize label clutter for peaceful aesthetic
```

### Desert Sunrise
```markdown
Create a "desert sunrise" palette for arid region mapping:

Colors should evoke:
- Warm desert morning light
- Sand and rock textures
- Sparse vegetation
- Clear skies

Feature styling:
- Water features: Precious blue (#0EA5E9)
- Vegetation: Drought-resistant green (#65A30D)
- Terrain: Warm sandstone tones
- High contrast for sun-bleached environment
```

### Urban Minimal
```markdown
Create an "urban minimal" palette for city mapping:

Colors should evoke:
- Clean, modern aesthetic
- High readability
- Professional appearance
- Accessibility first

Feature styling:
- Simplified color palette (3-4 primary colors)
- Strong contrast ratios
- Clear hierarchy
- Optimized for data visualization
```

## Accessibility Prompt

```markdown
Review this MapLibre style for accessibility compliance:
{style_json}

Check for:
1. WCAG AA contrast ratios (4.5:1 minimum)
2. Color blindness compatibility (protanopia, deuteranopia, tritanopia)
3. Visual hierarchy clarity
4. Text readability at all zoom levels
5. Symbol differentiation beyond color

Provide:
- Accessibility score
- Specific improvements needed
- Alternative color suggestions
- Symbol/pattern alternatives where needed
```

## Performance Optimization Prompt

```markdown
Optimize this MapLibre style for performance:
{style_json}

Target optimizations:
1. Reduce draw calls through layer consolidation
2. Optimize zoom-dependent styling
3. Minimize complex expressions
4. Efficient sprite usage
5. Memory usage reduction

Consider:
- Mobile device performance
- Large dataset handling
- Smooth zoom transitions
- Battery life impact

Provide optimized style with performance notes.
```

## Regional Adaptation Prompt

```markdown
Adapt this base style for regional characteristics:

Base style: {base_style}
Target region: {region}
Cultural considerations: {cultural_notes}

Adaptations needed:
1. Color preferences for the region
2. Typography appropriate for local languages
3. Symbol conventions
4. Cultural sensitivity considerations
5. Climate/terrain-appropriate styling

Provide culturally-adapted style variant.
```

## Error Recovery Prompt

```markdown
Style generation failed with error: {error_message}

Context:
- Features: {feature_types}
- Palette: {palette_mood}
- Tile schema: {schema_summary}

Provide:
1. Error diagnosis and likely cause
2. Fallback style recommendation
3. Minimal working style as backup
4. Debugging steps for resolution

Generate a simple, functional style that works with the given tile schema.
```

## Style Validation Prompt

```markdown
Validate this MapLibre style against the tile schema:

Style: {style_json}
Schema: {schema_json}

Validation checks:
1. Layer references match schema layer names
2. Attribute references exist in schema
3. Geometry types are compatible
4. Zoom ranges are logical
5. Expression syntax is valid

Provide:
- Validation results
- Compatibility issues
- Suggested fixes
- Performance warnings
``` 