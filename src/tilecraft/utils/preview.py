"""
Preview generation utilities.
"""

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class PreviewGenerator:
    """Generates previews and static maps from vector tiles."""
    
    def __init__(self, output_dir: Path):
        """
        Initialize preview generator.
        
        Args:
            output_dir: Directory to save previews
        """
        self.output_dir = output_dir
        
    def generate_static_map(self, mbtiles_path: Path, style_path: Path, 
                          bbox: tuple, width: int = 800, height: int = 600) -> Optional[Path]:
        """
        Generate static map preview.
        
        Args:
            mbtiles_path: Path to MBTiles file
            style_path: Path to MapLibre style JSON
            bbox: Bounding box (west, south, east, north)
            width: Image width in pixels
            height: Image height in pixels
            
        Returns:
            Path to generated preview image or None if failed
        """
        logger.info("Static map generation not yet implemented")
        # TODO: Implement static map generation using headless browser or similar
        return None
    
    def generate_html_preview(self, mbtiles_path: Path, style_path: Path) -> Path:
        """
        Generate interactive HTML preview.
        
        Args:
            mbtiles_path: Path to MBTiles file
            style_path: Path to MapLibre style JSON
            
        Returns:
            Path to generated HTML file
        """
        preview_path = self.output_dir / "preview.html"
        
        # Generate basic HTML preview
        html_content = self._create_html_template(mbtiles_path, style_path)
        
        with open(preview_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        logger.info(f"HTML preview generated: {preview_path}")
        return preview_path
    
    def _create_html_template(self, mbtiles_path: Path, style_path: Path) -> str:
        """
        Create HTML template for preview.
        
        Args:
            mbtiles_path: Path to MBTiles file
            style_path: Path to style JSON
            
        Returns:
            HTML content as string
        """
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>Tilecraft Preview</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://unpkg.com/maplibre-gl@4.4.1/dist/maplibre-gl.js"></script>
    <link href="https://unpkg.com/maplibre-gl@4.4.1/dist/maplibre-gl.css" rel="stylesheet">
    <style>
        body {{ margin: 0; padding: 0; }}
        #map {{ position: absolute; top: 0; bottom: 0; width: 100%; }}
        .info {{ 
            position: absolute; 
            top: 10px; 
            left: 10px; 
            background: rgba(255,255,255,0.9); 
            padding: 10px; 
            border-radius: 5px;
            font-family: Arial, sans-serif;
        }}
    </style>
</head>
<body>
    <div id="map"></div>
    <div class="info">
        <h3>Tilecraft Preview</h3>
        <p>MBTiles: {mbtiles_path.name}</p>
        <p>Style: {style_path.name}</p>
        <p><em>Note: This preview requires a local tile server</em></p>
    </div>
    
    <script>
        // TODO: Add MapLibre GL JS initialization
        // This would require serving the MBTiles through a tile server
        console.log('Preview HTML generated');
        console.log('MBTiles path: {mbtiles_path}');
        console.log('Style path: {style_path}');
    </script>
</body>
</html>""" 