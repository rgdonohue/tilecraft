"""
AI-powered OSM tag disambiguation.
"""

import logging

from tilecraft.models.config import FeatureType, TilecraftConfig

logger = logging.getLogger(__name__)


class TagDisambiguator:
    """Disambiguates OSM tags using AI and pattern matching."""

    def __init__(self, config: TilecraftConfig):
        """
        Initialize tag disambiguator.

        Args:
            config: Tilecraft configuration
        """
        self.config = config

        # Default tag mappings (can be enhanced with AI)
        self.tag_mappings = {
            FeatureType.RIVERS: {
                "waterway": ["river", "stream", "canal", "drain", "creek", "brook"],
            },
            FeatureType.FOREST: {
                "natural": ["wood", "forest", "scrub"],
                "landuse": ["forest", "wood"],
            },
            FeatureType.WATER: {
                "natural": ["water"],
                "waterway": ["*"],
            },
            FeatureType.LAKES: {
                "natural": ["water"],
                "water": ["lake", "pond", "reservoir"],
            },
            FeatureType.PARKS: {
                "leisure": ["park", "nature_reserve", "recreation_ground", "garden"],
                "boundary": ["national_park", "protected_area"],
            },
            FeatureType.ROADS: {
                "highway": ["*"],
            },
            FeatureType.BUILDINGS: {
                "building": ["*"],
            },
        }

    def get_tags_for_feature(self, feature_type: FeatureType) -> dict[str, list[str]]:
        """
        Get OSM tags for feature type.

        Args:
            feature_type: Feature type to get tags for

        Returns:
            Dictionary of tag filters
        """
        return self.tag_mappings.get(feature_type, {})

    def disambiguate_tags(
        self, feature_type: FeatureType, candidate_tags: list[dict[str, str]]
    ) -> list[dict[str, str]]:
        """
        Disambiguate potentially conflicting tags.

        Args:
            feature_type: Target feature type
            candidate_tags: List of tag dictionaries to evaluate

        Returns:
            Filtered list of relevant tags
        """
        logger.info(f"Disambiguating tags for {feature_type.value}")

        relevant_tags = []
        known_tags = self.get_tags_for_feature(feature_type)

        for tag_dict in candidate_tags:
            if self._is_relevant_tag(tag_dict, known_tags):
                relevant_tags.append(tag_dict)

        logger.info(
            f"Found {len(relevant_tags)} relevant tags for {feature_type.value}"
        )
        return relevant_tags

    def _is_relevant_tag(
        self, tag_dict: dict[str, str], known_tags: dict[str, list[str]]
    ) -> bool:
        """
        Check if tag dictionary is relevant for feature type.

        Args:
            tag_dict: Tag dictionary to check
            known_tags: Known tags for feature type

        Returns:
            True if tag is relevant
        """
        for key, values in known_tags.items():
            if key in tag_dict:
                tag_value = tag_dict[key]
                if "*" in values or tag_value in values:
                    return True

        return False

    def enhance_with_ai(self, feature_type: FeatureType) -> dict[str, list[str]]:
        """
        Enhance tag mappings using AI.

        Args:
            feature_type: Feature type to enhance

        Returns:
            Enhanced tag mappings
        """
        logger.info(f"AI tag enhancement not yet implemented for {feature_type.value}")
        # TODO: Implement AI-powered tag discovery and disambiguation
        return self.get_tags_for_feature(feature_type)

    def get_conflicting_tags(
        self, feature_types: list[FeatureType]
    ) -> dict[str, list[FeatureType]]:
        """
        Identify tags that could match multiple feature types.

        Args:
            feature_types: List of feature types to check

        Returns:
            Dictionary mapping tags to conflicting feature types
        """
        conflicts = {}

        for feature_type in feature_types:
            tags = self.get_tags_for_feature(feature_type)
            for key, values in tags.items():
                for value in values:
                    tag_str = f"{key}={value}" if value != "*" else key
                    if tag_str not in conflicts:
                        conflicts[tag_str] = []
                    conflicts[tag_str].append(feature_type)

        # Keep only actual conflicts (multiple feature types)
        return {tag: types for tag, types in conflicts.items() if len(types) > 1}
