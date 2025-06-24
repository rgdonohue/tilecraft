"""
Prompt templates for AI integration.
"""

from typing import List, Dict, Any

from tilecraft.models.config import FeatureType, PaletteConfig


class PromptTemplates:
    """Templates for AI prompts used in Tilecraft."""
    
    @staticmethod
    def schema_generation_prompt(feature_types: List[FeatureType], bbox_info: str) -> str:
        """
        Generate prompt for tile schema generation.
        
        Args:
            feature_types: List of feature types
            bbox_info: Bounding box description
            
        Returns:
            Schema generation prompt
        """
        feature_list = ", ".join([f.value for f in feature_types])
        
        return f"""Generate a vector tile schema for the following OpenStreetMap feature types: {feature_list}.

This schema will be used to generate vector tiles for a geographic region: {bbox_info}.

Requirements:
1. Include appropriate geometry types (point, linestring, polygon) for each feature
2. Suggest essential attributes for cartographic rendering
3. Recommend appropriate minzoom/maxzoom levels for each feature type
4. Consider zoom-dependent generalization strategies
5. Include appropriate simplification parameters for large-scale features

For each feature type, provide:
- Geometry type (point, linestring, or polygon)
- Recommended zoom levels (0-18)
- Essential attributes to preserve
- Simplification strategy for different zoom levels

Format the response as a structured JSON schema compatible with tippecanoe vector tile generation.

Focus on cartographic clarity and performance optimization for web mapping applications."""

    @staticmethod
    def style_generation_prompt(feature_types: List[FeatureType], palette: PaletteConfig, region_context: str) -> str:
        """
        Generate prompt for MapLibre style generation.
        
        Args:
            feature_types: List of feature types
            palette: Palette configuration
            region_context: Geographic context
            
        Returns:
            Style generation prompt
        """
        feature_list = ", ".join([f.value for f in feature_types])
        
        base_prompt = f"""Generate a MapLibre GL JS style JSON for vector tiles representing {feature_list} in {region_context} using a '{palette.name}' palette.

Style Requirements:
1. Create a cohesive color scheme that reflects the '{palette.name}' mood
2. Ensure proper contrast ratios for accessibility (WCAG AA compliance)
3. Use zoom-dependent styling for optimal performance
4. Include appropriate typography with minimalist sans-serif fonts
5. Reduce label clutter while maintaining readability
6. Consider cartographic best practices for the feature types

Feature-specific styling guidelines:"""

        # Add feature-specific guidelines
        guidelines = {
            FeatureType.RIVERS: "Rivers should have flowing, organic appearance with subtle glow effects",
            FeatureType.FOREST: "Forests should use natural green tones with texture variations",
            FeatureType.WATER: "Water bodies should appear calm and reflective",
            FeatureType.LAKES: "Lakes should be distinguished from other water with deeper tones",
            FeatureType.PARKS: "Parks should feel inviting with lighter, more vibrant greens",
            FeatureType.ROADS: "Roads should be subtle but clearly defined hierarchy",
            FeatureType.BUILDINGS: "Buildings should have consistent styling with appropriate shadows"
        }
        
        for feature_type in feature_types:
            if feature_type in guidelines:
                base_prompt += f"\n- {feature_type.value.title()}: {guidelines[feature_type]}"
        
        base_prompt += f"""

Palette mood interpretation for '{palette.name}':
"""
        
        # Add palette-specific guidance
        palette_guidance = {
            "subalpine dusk": "Cool mountain colors with muted blues, greens, and purples. Evening atmosphere with subtle gradients.",
            "desert sunset": "Warm earth tones with oranges, reds, and sandy colors. High contrast with dramatic lighting.",
            "pacific northwest": "Deep forest greens, ocean blues, and misty grays. Emphasize natural, organic feel.",
            "urban midnight": "High contrast dark theme with bright accent colors. Modern, tech-forward aesthetic.",
            "arctic": "Cool blues and whites with ice-like clarity. Minimal, clean design.",
            "tropical": "Vibrant greens and blues with high saturation. Lush, energetic feel."
        }
        
        guidance = palette_guidance.get(palette.name.lower(), "Interpret the palette name to create an appropriate mood and color scheme.")
        base_prompt += guidance
        
        base_prompt += """

Output a complete MapLibre GL JS style JSON that includes:
1. Appropriate source configuration for vector tiles
2. Background layer with palette-appropriate color
3. Feature layers with proper styling
4. Zoom-dependent expressions for dynamic styling
5. Label layers where appropriate
6. Proper layer ordering for optimal rendering

Ensure the style is production-ready and follows MapLibre GL JS best practices."""

        return base_prompt

    @staticmethod
    def tag_disambiguation_prompt(feature_type: FeatureType) -> str:
        """
        Generate prompt for OSM tag disambiguation.
        
        Args:
            feature_type: Feature type to disambiguate
            
        Returns:
            Tag disambiguation prompt
        """
        return f"""Given the feature type '{feature_type.value}', identify all relevant OpenStreetMap tags including:

1. Primary tags (most common and standard)
2. Synonyms and variations 
3. Regional variants
4. Common misspellings or alternative spellings
5. Related tags that might overlap
6. Deprecated tags that are still in use

For each tag, provide:
- Tag key and value (e.g., natural=wood)
- Frequency/popularity (common, uncommon, rare)
- Geographic regions where it's prevalent
- Notes on usage context

Also identify potential conflicts or ambiguities:
- Tags that could match multiple feature types
- Cases where manual verification might be needed
- Recommended resolution strategies

Format the response as a structured list that can be used for automated tag matching and filtering in OSM data processing.

Focus on maximizing feature capture while minimizing false positives."""

    @staticmethod
    def validation_prompt(generated_content: str, content_type: str) -> str:
        """
        Generate prompt for validating AI-generated content.
        
        Args:
            generated_content: Content to validate
            content_type: Type of content (schema, style, tags)
            
        Returns:
            Validation prompt
        """
        return f"""Please review and validate the following {content_type}:

{generated_content}

Check for:
1. Technical correctness and specification compliance
2. Cartographic best practices
3. Performance implications
4. Accessibility considerations
5. Potential edge cases or issues

Provide:
1. Overall assessment (valid/needs_revision/invalid)
2. Specific issues found with line numbers/locations
3. Suggested improvements
4. Risk assessment for production use

Focus on practical usability for web mapping applications and adherence to industry standards."""

    @staticmethod
    def error_analysis_prompt(error_message: str, context: str) -> str:
        """
        Generate prompt for AI-assisted error analysis.
        
        Args:
            error_message: Error message to analyze
            context: Context where error occurred
            
        Returns:
            Error analysis prompt
        """
        return f"""Analyze this error that occurred during {context}:

Error: {error_message}

Please provide:
1. Root cause analysis
2. Possible solutions or workarounds
3. Prevention strategies for the future
4. Related issues that might arise
5. Code suggestions if applicable

Focus on practical solutions that can be implemented immediately and long-term improvements to prevent similar issues.""" 