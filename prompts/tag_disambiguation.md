# OSM Tag Disambiguation Prompts

## Core Disambiguation Prompt

```markdown
Analyze OSM tags for feature type "{feature_type}" and provide disambiguation mapping:

Context: Processing OSM data for vector tile generation
Goal: Map inconsistent/variant OSM tags to standardized feature categories

For feature type "{feature_type}", identify:
1. Primary canonical tags
2. Common variants and synonyms  
3. Regional variations
4. Common misspellings or inconsistencies
5. Overlapping tags that represent the same feature

Provide mapping table: variant_tag -> canonical_category

Consider geographic region: {region} (may have regional tagging patterns)
```

## Feature-Specific Disambiguation

### Forest/Woodland Disambiguation
```markdown
Disambiguate forest-related OSM tags:

Common tag variations:
- landuse=forest
- natural=wood
- leisure=nature_reserve (forested areas)
- natural=scrub (transitional forests)
- landuse=forestry

Regional variations:
- European: Often uses natural=wood
- North American: Often uses landuse=forest
- Protected areas: leisure=nature_reserve + forest characteristics

Conflicts to resolve:
- landuse=forest vs natural=wood (same polygon)
- natural=wood + landuse=forestry (managed forest)

Output standardized mapping for "forest" feature category.
```

### Water Feature Disambiguation
```markdown
Disambiguate water-related OSM tags:

Waterway tags:
- waterway=river (major rivers)
- waterway=stream (minor watercourses)
- waterway=canal (artificial waterways)
- waterway=drain (drainage channels)

Water body tags:
- natural=water + water=lake
- natural=water + water=pond
- landuse=reservoir
- natural=wetland (different category)

Conflicts:
- Missing water=* on natural=water features
- waterway=river vs natural=water (river areas vs centerlines)

Output mapping for "rivers" and "water" categories.
```

### Transportation Disambiguation
```markdown
Disambiguate transportation OSM tags:

Road hierarchy:
- highway=motorway/trunk/primary/secondary/tertiary
- highway=residential/unclassified
- highway=track/path/footway

Common issues:
- Inconsistent highway classification between regions
- highway=road (needs reclassification)
- Missing surface/access information

Regional patterns:
- Rural areas: Often over-classify minor roads
- Urban areas: Complex access restrictions

Output standardized road categorization.
```

## Fuzzy Matching Prompt

```markdown
Implement fuzzy matching for OSM tag values:

Input tag: {key}={value}
Context: Feature extraction for {feature_type}

Fuzzy matching strategy:
1. Exact match first
2. Case-insensitive matching
3. Common abbreviations (e.g., "St" -> "Street")
4. Typo tolerance (Levenshtein distance ≤ 2)
5. Language variations (multilingual tag values)

Known patterns for this feature type:
{known_patterns}

Provide:
- Match confidence score (0-1)
- Suggested canonical value
- Reasoning for the match
```

## Confidence Scoring Prompt

```markdown
Score the confidence of this tag disambiguation:

Original tags: {original_tags}
Proposed mapping: {proposed_mapping}
Feature type: {feature_type}
Geographic region: {region}

Confidence factors:
1. Tag frequency in OSM (common vs rare tags)
2. Regional appropriateness
3. Semantic consistency
4. Geometry type compatibility
5. Supporting evidence from related tags

Provide:
- Overall confidence score (0-1)
- Risk assessment for misclassification
- Alternative interpretations if confidence < 0.8
- Recommended human review threshold
```

## Conflict Resolution Prompt

```markdown
Resolve conflicting OSM tags on the same feature:

Feature geometry: {geometry_type}
Conflicting tags: {conflicting_tags}
Context: {feature_context}

Common conflict patterns:
1. Multiple land use designations
2. Natural vs artificial classifications
3. Current vs historical use
4. Administrative vs physical characteristics

Resolution strategy:
1. Identify primary vs secondary characteristics
2. Consider geometry type appropriateness  
3. Apply regional mapping conventions
4. Maintain feature integrity for visualization

Provide:
- Primary classification decision
- Secondary attributes to preserve
- Reasoning for resolution
- Confidence in decision
```

## Quality Assessment Prompt

```markdown
Assess the quality of this tag disambiguation result:

Input data: {input_summary}
Disambiguation results: {results_summary}
Processing statistics: {stats}

Quality metrics:
1. Coverage: % of features successfully classified
2. Consistency: Similar features receive same classification
3. Completeness: Essential attributes preserved
4. Accuracy: Spot-check against known ground truth
5. Performance: Processing time and memory usage

Red flags to check:
- Unexpectedly high number of unclassified features
- Classification inconsistencies within same region
- Loss of important attributes
- Excessive processing time

Provide quality report with recommendations.
```

## Error Handling Prompt

```markdown
Handle tag disambiguation errors:

Error type: {error_type}
Context: {error_context}
Failed input: {failed_input}

Common error types:
1. Unknown tag combinations
2. Ambiguous feature classification
3. Missing required attributes
4. Geometry-tag incompatibility

Recovery strategies:
1. Fallback to less specific classification
2. Flag for manual review
3. Use geographic context for hints
4. Apply most common classification for area

Provide:
- Error analysis
- Recovery recommendation
- Fallback classification
- Prevention strategy for similar errors
``` 