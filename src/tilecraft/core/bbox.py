"""
Bounding box utilities for OSM data processing.
"""

from pathlib import Path
from typing import List, Tuple

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
    with open(output_path, 'w') as f:
        f.write(poly_content)
        
    return output_path


def bbox_to_overpass_query(bbox: BoundingBox, feature_types: List[str]) -> str:
    """
    Generate Overpass API query for bounding box and features.
    
    Args:
        bbox: Bounding box for query
        feature_types: List of feature types to query
        
    Returns:
        Overpass QL query string
    """
    # Construct query based on feature types
    queries = []
    
    for feature_type in feature_types:
        if feature_type == "rivers":
            queries.append('way["waterway"~"^(river|stream|canal)$"]')
        elif feature_type == "forest":
            queries.append('way["natural"~"^(wood|forest)$"]')
            queries.append('way["landuse"="forest"]')
        elif feature_type == "water":
            queries.append('way["natural"="water"]')
        elif feature_type == "lakes":
            queries.append('way["natural"="water"]["water"="lake"]')
        elif feature_type == "parks":
            queries.append('way["leisure"~"^(park|nature_reserve)$"]')
        elif feature_type == "roads":
            queries.append('way["highway"]')
        elif feature_type == "buildings":
            queries.append('way["building"]')
    
    # Build complete query
    bbox_str = f"{bbox.south},{bbox.west},{bbox.north},{bbox.east}"
    
    query_parts = []
    for q in queries:
        query_parts.append(f"({q}({bbox_str}););")
    
    query = f"""[out:xml][timeout:300];
(
{''.join(query_parts)}
);
out geom;
"""
    
    return query


def get_bbox_center_zoom(bbox: BoundingBox) -> Tuple[float, float, int]:
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