"""
Bounding box utilities for OSM data processing.
"""

from pathlib import Path

from tilecraft.models.config import BoundingBox


def validate_bbox(bbox: BoundingBox) -> bool:
    """
    Validate bounding box coordinates and constraints.

    Args:
        bbox: Bounding box to validate

    Returns:
        True if valid, False otherwise
    """
    # Basic coordinate validation is handled by Pydantic
    # Additional validation can be added here

    # Check if area is reasonable (not too large or too small)
    area = bbox.area_degrees
    if area > 100:  # More than 100 square degrees
        return False
    if area < 0.0001:  # Less than 0.0001 square degrees
        return False

    return True


def bbox_to_poly(bbox: BoundingBox, output_path: Path) -> Path:
    """
    Convert bounding box to .poly file format for osmium.

    Args:
        bbox: Bounding box to convert
        output_path: Path to write .poly file

    Returns:
        Path to created .poly file
    """
    poly_content = f"""polygon
1
  {bbox.west}  {bbox.south}
  {bbox.west}  {bbox.north}
  {bbox.east}  {bbox.north}
  {bbox.east}  {bbox.south}
  {bbox.west}  {bbox.south}
END
END
"""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write(poly_content)

    return output_path


def bbox_to_overpass_query(bbox: BoundingBox, feature_types: list[str]) -> str:
    """
    Generate Overpass API query for bounding box and features.

    Args:
        bbox: Bounding box for query
        feature_types: List of feature types to query

    Returns:
        Overpass QL query string
    """
    # Comprehensive mapping of feature types to Overpass queries
    feature_queries = {
        # Water Features
        "rivers": [
            'way["waterway"~"^(river|stream|canal|drain|ditch|waterfall)$"]'
        ],
        "water": [
            'way["natural"="water"]',
            'way["landuse"~"^(reservoir|basin)$"]'
        ],
        "lakes": [
            'way["natural"="water"]["water"~"^(lake|pond|lagoon)$"]',
            'way["natural"="water"][!waterway]'
        ],
        "wetlands": [
            'way["natural"~"^(wetland|marsh|swamp)$"]'
        ],
        "waterways": [
            'way["waterway"~"^(river|stream|canal|drain|ditch|rapids|waterfall)$"]'
        ],
        "coastline": [
            'way["natural"~"^(coastline|beach|bay)$"]'
        ],
        
        # Natural Features
        "forest": [
            'way["natural"~"^(wood|forest|scrub)$"]',
            'way["landuse"~"^(forest|forestry)$"]'
        ],
        "woods": [
            'way["natural"~"^(wood|forest)$"]'
        ],
        "mountains": [
            'node["natural"~"^(peak|ridge|saddle|volcano)$"]',
            'way["natural"~"^(peak|ridge|saddle|volcano)$"]'
        ],
        "peaks": [
            'node["natural"~"^(peak|volcano)$"]',
            'way["natural"~"^(peak|volcano)$"]'
        ],
        "cliffs": [
            'way["natural"~"^(cliff|rock|scree|stone)$"]'
        ],
        "beaches": [
            'way["natural"~"^(beach|sand|shingle)$"]'
        ],
        "glaciers": [
            'way["natural"="glacier"]'
        ],
        "volcanoes": [
            'node["natural"="volcano"]',
            'way["natural"="volcano"]'
        ],
        
        # Land Use
        "parks": [
            'way["leisure"~"^(park|nature_reserve|recreation_ground|garden)$"]',
            'way["boundary"~"^(national_park|protected_area)$"]'
        ],
        "farmland": [
            'way["landuse"~"^(farmland|orchard|vineyard|plant_nursery|greenhouse_horticulture)$"]'
        ],
        "residential": [
            'way["landuse"="residential"]'
        ],
        "commercial": [
            'way["landuse"~"^(commercial|retail)$"]'
        ],
        "industrial": [
            'way["landuse"~"^(industrial|port|quarry)$"]'
        ],
        "military": [
            'way["landuse"="military"]',
            'way["military"]'
        ],
        "cemeteries": [
            'way["landuse"="cemetery"]',
            'way["amenity"="grave_yard"]'
        ],
        
        # Transportation
        "roads": [
            'way["highway"~"^(motorway|trunk|primary|secondary|tertiary|unclassified|residential|service|track)$"]'
        ],
        "highways": [
            'way["highway"~"^(motorway|motorway_link|trunk|trunk_link)$"]'
        ],
        "railways": [
            'way["railway"~"^(rail|tram|light_rail|subway|monorail|narrow_gauge|abandoned)$"]'
        ],
        "airports": [
            'way["aeroway"~"^(aerodrome|runway|taxiway|terminal|gate|apron)$"]',
            'node["aeroway"~"^(aerodrome|gate)$"]'
        ],
        "bridges": [
            'way["bridge"="yes"]',
            'way["man_made"="bridge"]'
        ],
        "tunnels": [
            'way["tunnel"="yes"]',
            'way["man_made"="tunnel"]'
        ],
        "paths": [
            'way["highway"~"^(path|footway|cycleway|bridleway|steps)$"]'
        ],
        "cycleways": [
            'way["highway"="cycleway"]',
            'way["cycleway"]'
        ],
        
        # Built Environment
        "buildings": [
            'way["building"]'
        ],
        "churches": [
            'way["building"~"^(church|cathedral|chapel)$"]',
            'way["amenity"="place_of_worship"]',
            'node["amenity"="place_of_worship"]'
        ],
        "schools": [
            'way["building"="school"]',
            'way["amenity"~"^(school|kindergarten|university|college)$"]',
            'node["amenity"~"^(school|kindergarten|university|college)$"]'
        ],
        "hospitals": [
            'way["building"="hospital"]',
            'way["amenity"~"^(hospital|clinic|doctors)$"]',
            'node["amenity"~"^(hospital|clinic|doctors)$"]'
        ],
        "universities": [
            'way["building"~"^(university|college)$"]',
            'way["amenity"~"^(university|college)$"]',
            'node["amenity"~"^(university|college)$"]'
        ],
        
        # Amenities
        "restaurants": [
            'way["amenity"~"^(restaurant|fast_food|cafe|bar|pub|food_court)$"]',
            'node["amenity"~"^(restaurant|fast_food|cafe|bar|pub|food_court)$"]'
        ],
        "shops": [
            'way["shop"]',
            'way["building"~"^(retail|shop)$"]',
            'way["amenity"="marketplace"]',
            'node["shop"]',
            'node["amenity"="marketplace"]'
        ],
        "hotels": [
            'way["tourism"~"^(hotel|motel|hostel|guest_house)$"]',
            'way["building"="hotel"]',
            'node["tourism"~"^(hotel|motel|hostel|guest_house)$"]'
        ],
        "banks": [
            'way["amenity"~"^(bank|atm)$"]',
            'way["building"="bank"]',
            'node["amenity"~"^(bank|atm)$"]'
        ],
        "fuel_stations": [
            'way["amenity"="fuel"]',
            'way["building"="fuel"]',
            'node["amenity"="fuel"]'
        ],
        "post_offices": [
            'way["amenity"="post_office"]',
            'way["building"="post_office"]',
            'node["amenity"="post_office"]'
        ],
        
        # Recreation
        "playgrounds": [
            'way["leisure"="playground"]',
            'node["leisure"="playground"]'
        ],
        "sports_fields": [
            'way["leisure"~"^(sports_centre|stadium|pitch)$"]',
            'way["sport"]',
            'node["leisure"~"^(sports_centre|stadium)$"]'
        ],
        "golf_courses": [
            'way["leisure"="golf_course"]',
            'way["sport"="golf"]'
        ],
        "stadiums": [
            'way["leisure"="stadium"]',
            'way["building"="stadium"]',
            'node["leisure"="stadium"]'
        ],
        "swimming_pools": [
            'way["leisure"="swimming_pool"]',
            'way["amenity"="swimming_pool"]',
            'node["amenity"="swimming_pool"]'
        ],
        
        # Infrastructure
        "power_lines": [
            'way["power"~"^(line|cable|transmission|substation)$"]',
            'way["man_made"="transmission_line"]',
            'node["power"~"^(substation|tower)$"]'
        ],
        "wind_turbines": [
            'way["generator:source"="wind"]',
            'way["man_made"="wind_turbine"]',
            'node["man_made"="wind_turbine"]'
        ],
        "solar_farms": [
            'way["generator:source"="solar"]',
            'way["man_made"="solar_panel"]',
            'way["landuse"="industrial"]["generator:source"="solar"]',
            'node["man_made"="solar_panel"]'
        ],
        "dams": [
            'way["waterway"="dam"]',
            'way["man_made"="dam"]',
            'node["waterway"="dam"]'
        ],
        "barriers": [
            'way["barrier"~"^(wall|fence|hedge|retaining_wall|city_wall)$"]'
        ],
        
        # Administrative
        "boundaries": [
            'way["boundary"~"^(administrative|political|postal_code)$"]'
        ],
        "protected_areas": [
            'way["boundary"~"^(protected_area|national_park)$"]',
            'way["leisure"="nature_reserve"]'
        ]
    }
    
    # Collect all queries for requested feature types
    all_queries = []
    unrecognized_features = []
    
    for feature_type in feature_types:
        if feature_type in feature_queries:
            all_queries.extend(feature_queries[feature_type])
        else:
            unrecognized_features.append(feature_type)
    
    # Log warning for unrecognized features
    if unrecognized_features:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Unrecognized feature types (no Overpass query available): {unrecognized_features}")
        logger.info(f"Available feature types: {sorted(feature_queries.keys())}")
    
    # If no valid queries, return minimal query to avoid empty results
    if not all_queries:
        return f"""[out:xml][timeout:300];
(
  // No valid feature types provided
);
out geom;
"""
    
    # Build complete query
    bbox_str = f"{bbox.south},{bbox.west},{bbox.north},{bbox.east}"
    
    query_parts = []
    for query in all_queries:
        query_parts.append(f"({query}({bbox_str}););")
    
    query = f"""[out:xml][timeout:300];
(
{''.join(query_parts)}
);
out meta geom;
"""
    
    return query


def get_bbox_center_zoom(bbox: BoundingBox) -> tuple[float, float, int]:
    """
    Calculate appropriate center point and zoom level for bbox.

    Args:
        bbox: Bounding box

    Returns:
        Tuple of (longitude, latitude, zoom_level)
    """
    center_lon, center_lat = bbox.center

    # Estimate zoom level based on area
    area = bbox.area_degrees
    if area > 10:
        zoom = 8
    elif area > 1:
        zoom = 10
    elif area > 0.1:
        zoom = 12
    else:
        zoom = 14

    return center_lon, center_lat, zoom
