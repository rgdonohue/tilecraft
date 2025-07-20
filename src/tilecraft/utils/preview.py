"""
Preview generation utilities.
"""

import json
import logging
import sqlite3
from pathlib import Path
from typing import Optional

from tilecraft.models.config import BoundingBox

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
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_static_map(
        self,
        mbtiles_path: Path,
        style_path: Path,
        bbox: tuple,
        width: int = 800,
        height: int = 600,
    ) -> Optional[Path]:
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

    def generate_html_preview(
        self, mbtiles_path: Path, style_path: Optional[Path] = None, bbox: Optional[BoundingBox] = None
    ) -> Path:
        """
        Generate interactive HTML preview with tileserver-gl-light integration.

        Args:
            mbtiles_path: Path to MBTiles file
            style_path: Path to MapLibre style JSON
            bbox: Optional bounding box for initial view

        Returns:
            Path to generated HTML file
        """
        preview_path = self.output_dir / "preview.html"

        # Extract metadata from MBTiles if bbox not provided
        if bbox is None:
            bbox = self._extract_bounds_from_mbtiles(mbtiles_path)

        # Generate tileserver-gl-light config
        self._create_tileserver_config(mbtiles_path, style_path)

        # Extract source layer name from mbtiles
        source_layer = self._extract_source_layer_name(mbtiles_path)

        # Generate HTML preview optimized for tileserver-gl-light
        html_content = self._create_tileserver_html_template(
            mbtiles_path, style_path, bbox, source_layer
        )

        with open(preview_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        # Generate setup instructions
        self._create_setup_instructions(mbtiles_path)

        logger.info(f"HTML preview generated: {preview_path}")
        return preview_path

    def _extract_bounds_from_mbtiles(self, mbtiles_path: Path) -> BoundingBox:
        """Extract bounds from MBTiles metadata."""
        try:
            conn = sqlite3.connect(mbtiles_path)
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT value FROM metadata WHERE name = 'bounds'"
                )
                result = cursor.fetchone()
                if result:
                    bounds = [float(x) for x in result[0].split(",")]
                    return BoundingBox(
                        west=bounds[0],
                        south=bounds[1],
                        east=bounds[2],
                        north=bounds[3],
                    )
            finally:
                conn.close()
        except Exception as e:
            logger.warning(f"Could not extract bounds from MBTiles: {e}")

        # Default fallback bounds (world view)
        return BoundingBox(west=-180, south=-85, east=180, north=85)

    def _extract_source_layer_name(self, mbtiles_path: Path) -> str:
        """Extract the source layer name from MBTiles metadata."""
        try:
            conn = sqlite3.connect(mbtiles_path)
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT value FROM metadata WHERE name = 'json'"
                )
                result = cursor.fetchone()
                if result:
                    metadata = json.loads(result[0])
                    vector_layers = metadata.get("vector_layers", [])
                    if vector_layers:
                        # Return the first vector layer's ID
                        return vector_layers[0].get("id", mbtiles_path.stem)
            finally:
                conn.close()
        except Exception as e:
            logger.warning(f"Could not extract source layer name from MBTiles: {e}")
        
        # Fallback to filename without extension
        return mbtiles_path.stem

    def _copy_style_file(self, style_path: Path) -> Path:
        """Copy style file to output directory for relative access."""
        style_copy_path = self.output_dir / "style.json"
        
        # Read and potentially modify the style
        with open(style_path, "r") as f:
            style_data = json.load(f)
        
        # Update source URLs to use local tile server
        if "sources" in style_data:
            for source_name, source_config in style_data["sources"].items():
                if source_config.get("type") == "vector":
                    # Point to local tile server
                    source_config["url"] = f"http://localhost:8080/{source_name}"
        
        # Write modified style
        with open(style_copy_path, "w") as f:
            json.dump(style_data, f, indent=2)
        
        return style_copy_path

    def _create_tile_server_script(self, mbtiles_path: Path) -> None:
        """Create a simple tile server script."""
        server_script = self.output_dir / "start_tile_server.py"
        
        script_content = f'''#!/usr/bin/env python3
"""
Simple tile server for MBTiles preview.
Requires: pip install flask sqlite3
"""

import sqlite3
from flask import Flask, Response, send_from_directory
from pathlib import Path

app = Flask(__name__)
MBTILES_PATH = Path("{mbtiles_path.absolute()}")

@app.route("/tiles/<int:z>/<int:x>/<int:y>.pbf")
def get_tile(z, x, y):
    """Serve vector tiles from MBTiles."""
    try:
        with sqlite3.connect(MBTILES_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT tile_data FROM tiles WHERE zoom_level=? AND tile_column=? AND tile_row=?",
                (z, x, (1 << z) - 1 - y)  # TMS to XYZ conversion
            )
            tile_data = cursor.fetchone()
            
            if tile_data:
                return Response(
                    tile_data[0],
                    mimetype="application/x-protobuf",
                    headers={{"Access-Control-Allow-Origin": "*"}}
                )
            else:
                return Response("Tile not found", status=404)
    except Exception as e:
        return Response(f"Error: {{e}}", status=500)

@app.route("/")
def serve_preview():
    """Serve the preview HTML."""
    return send_from_directory(".", "preview.html")

@app.route("/<path:filename>")
def serve_static(filename):
    """Serve static files."""
    return send_from_directory(".", filename)

if __name__ == "__main__":
    print("Starting tile server at http://localhost:8080")
    print("Open http://localhost:8080 in your browser to view the preview")
    app.run(host="localhost", port=8080, debug=False)
'''

        with open(server_script, "w") as f:
            f.write(script_content)
        
        # Make script executable
        server_script.chmod(0o755)
        
        logger.info(f"Tile server script created: {server_script}")

    def _create_tileserver_config(self, mbtiles_path: Path, style_path: Path) -> None:
        """Create tileserver-gl-light configuration file."""
        config_path = self.output_dir / "config.json"
        
        # Extract tileset name from mbtiles filename
        tileset_name = mbtiles_path.stem
        
        # Create tileserver-gl-light config
        config = {
            "options": {
                "paths": {
                    "mbtiles": str(mbtiles_path.parent.absolute())
                },
                "domains": ["localhost:8080"],
                "formatQuality": {
                    "jpeg": 80,
                    "webp": 90
                },
                "maxzoom": 18,
                "maxsize": 2048,
                "pbfAlias": "pbf"
            },
            "styles": {},
            "data": {}
        }
        
        # Add MBTiles data source
        config["data"][tileset_name] = {
            "mbtiles": mbtiles_path.name
        }
        
        # Add style if it exists
        if style_path and style_path.exists():
            style_name = f"{tileset_name}_style"
            style_copy_path = self.output_dir / "styles" / f"{style_name}.json"
            
            # Create styles directory
            style_copy_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy and modify style for tileserver-gl-light
            with open(style_path, "r") as f:
                style_data = json.load(f)
            
            # Update sources to use tileserver-gl-light URLs
            if "sources" in style_data:
                for source_name, source_config in style_data["sources"].items():
                    if source_config.get("type") == "vector":
                        source_config["url"] = f"mbtiles://{{{tileset_name}}}"
            
            # Write modified style
            with open(style_copy_path, "w") as f:
                json.dump(style_data, f, indent=2)
            
            config["styles"][style_name] = {
                "style": f"styles/{style_name}.json",
                "tilejson": {
                    "type": "baselayer"
                }
            }
        
        # Write config file
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"Tileserver-gl-light config created: {config_path}")

    def _create_setup_instructions(self, mbtiles_path: Path) -> None:
        """Create setup instructions for tileserver-gl-light."""
        instructions_path = self.output_dir / "README.md"
        
        tileset_name = mbtiles_path.stem
        
        instructions = f"""# Tilecraft Preview

## Quick Start with tileserver-gl-light

### 1. Install tileserver-gl-light
```bash
npm install -g tileserver-gl-light
```

### 2. Start the server (Option A - Simple)
```bash
# Point directly at your mbtiles file or directory
tileserver-gl-light {mbtiles_path.absolute()}
```

### 2. Start the server (Option B - With config)
```bash
cd {self.output_dir.absolute()}
tileserver-gl-light --config config.json
```

### 3. View your tiles
- Open http://localhost:8080 in your browser
- Select your dataset: `{tileset_name}`
- Or view directly at: http://localhost:8080/data/{tileset_name}/

## Alternative: Use the HTML preview
- Open `preview.html` in your browser
- It will automatically connect to tileserver-gl-light when running

## Files included:
- `config.json` - Tileserver-gl-light configuration (optional)
- `preview.html` - Interactive HTML preview
- `styles/` - MapLibre GL styles (if generated)

## Troubleshooting:
- Ensure tileserver-gl-light is installed and running on port 8080
- Option A (direct file) is simpler and avoids config issues
- View browser console for any loading errors
"""
        
        with open(instructions_path, "w") as f:
            f.write(instructions)
        
        logger.info(f"Setup instructions created: {instructions_path}")

    def _create_tileserver_html_template(
        self, mbtiles_path: Path, style_path: Optional[Path], bbox: BoundingBox, source_layer: str
    ) -> str:
        """Create HTML template optimized for tileserver-gl-light."""
        center_lng = (bbox.west + bbox.east) / 2
        center_lat = (bbox.south + bbox.north) / 2
        
        # Calculate appropriate zoom level based on bbox size
        lng_diff = abs(bbox.east - bbox.west)
        lat_diff = abs(bbox.north - bbox.south)
        max_diff = max(lng_diff, lat_diff)
        
        # Rough zoom calculation
        if max_diff > 10:
            zoom = 5
        elif max_diff > 1:
            zoom = 8
        elif max_diff > 0.1:
            zoom = 11
        else:
            zoom = 14

        tileset_name = mbtiles_path.stem
        style_name = f"{tileset_name}_style"

        return f"""<!DOCTYPE html>
<html>
<head>
    <title>Tilecraft Preview - {tileset_name}</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://unpkg.com/maplibre-gl@4.4.1/dist/maplibre-gl.js"></script>
    <link href="https://unpkg.com/maplibre-gl@4.4.1/dist/maplibre-gl.css" rel="stylesheet">
    <style>
        body {{ margin: 0; padding: 0; font-family: Arial, sans-serif; }}
        #map {{ position: absolute; top: 0; bottom: 0; width: 100%; }}
        .info {{
            position: absolute;
            top: 10px;
            left: 10px;
            background: rgba(255,255,255,0.95);
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            max-width: 350px;
            z-index: 1000;
        }}
        .info h3 {{ margin: 0 0 10px 0; color: #333; }}
        .info p {{ margin: 5px 0; font-size: 14px; color: #666; }}
        .server-status {{ padding: 8px; border-radius: 4px; margin-top: 10px; }}
        .server-offline {{ background: #ffebee; color: #c62828; }}
        .server-online {{ background: #e8f5e8; color: #2e7d32; }}
        .instructions {{ margin-top: 10px; font-size: 12px; }}
        .instructions code {{ background: #f5f5f5; padding: 2px 4px; border-radius: 3px; }}
        .toggle-btn {{ 
            background: #007acc; 
            color: white; 
            border: none; 
            padding: 5px 10px; 
            border-radius: 3px; 
            cursor: pointer; 
            margin-top: 5px;
        }}
    </style>
</head>
<body>
    <div id="map"></div>
    <div class="info">
        <h3>🗺️ Tilecraft Preview</h3>
        <p><strong>Dataset:</strong> {tileset_name}</p>
        <p><strong>Bounds:</strong> {bbox.west:.3f}, {bbox.south:.3f}, {bbox.east:.3f}, {bbox.north:.3f}</p>
        
        <div id="server-status" class="server-status server-offline">
            ⚠️ Tileserver-gl-light offline
        </div>
        
        <div class="instructions">
            <strong>To view tiles:</strong><br>
            1. Install: <code>npm install -g tileserver-gl-light</code><br>
            2. Run: <code>tileserver-gl-light --config config.json</code><br>
            3. Open: <code>http://localhost:8080</code>
        </div>
        
        <button id="toggle-info" class="toggle-btn">Hide Info</button>
    </div>

    <script>
        // Initialize MapLibre GL with fallback
        const map = new maplibregl.Map({{
            container: 'map',
            style: {{
                "version": 8,
                "sources": {{
                    "osm": {{
                        "type": "raster",
                        "tiles": ["https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png"],
                        "tileSize": 256,
                        "attribution": "© OpenStreetMap contributors"
                    }}
                }},
                "layers": [{{
                    "id": "osm-background",
                    "type": "raster",
                    "source": "osm"
                }}]
            }},
            center: [{center_lng}, {center_lat}],
            zoom: {zoom}
        }});

        map.addControl(new maplibregl.NavigationControl());
        map.addControl(new maplibregl.ScaleControl());

        // Try to connect to tileserver-gl-light
        let customStyleLoaded = false;

        async function loadTileserverStyle() {{
            if (customStyleLoaded) return;
            
            try {{
                // Try style endpoint first
                const styleResponse = await fetch('http://localhost:8080/styles/{style_name}/style.json');
                if (styleResponse.ok) {{
                    const style = await styleResponse.json();
                    map.setStyle(style);
                    updateServerStatus('✅ Tileserver-gl-light connected (with style)');
                    customStyleLoaded = true;
                    
                    // Center map on the actual data bounds
                    map.fitBounds([
                        [{bbox.west}, {bbox.south}],
                        [{bbox.east}, {bbox.north}]
                    ], {{
                        padding: 50,
                        duration: 1000
                    }});
                    return;
                }}
                
                // Fallback: try to load raw tiles
                const tileResponse = await fetch('http://localhost:8080/data/{tileset_name}/0/0/0.pbf');
                if (tileResponse.ok || tileResponse.status === 404) {{
                    // Server is running, create basic style
                    const basicStyle = {{
                        "version": 8,
                        "sources": {{
                            "osm": {{
                                "type": "raster",
                                "tiles": ["https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png"],
                                "tileSize": 256,
                                "attribution": "© OpenStreetMap contributors"
                            }},
                            "tilecraft": {{
                                "type": "vector",
                                "tiles": ["http://localhost:8080/data/{tileset_name}/{{z}}/{{x}}/{{y}}.pbf"]
                            }}
                        }},
                        "layers": [
                            {{
                                "id": "osm-background",
                                "type": "raster",
                                "source": "osm"
                            }},
                            {{
                                "id": "tilecraft-lines",
                                "type": "line",
                                "source": "tilecraft",
                                "source-layer": "{source_layer}",
                                "filter": ["in", ["geometry-type"], ["literal", ["LineString", "MultiLineString"]]],
                                "paint": {{
                                    "line-color": "#ff6b6b",
                                    "line-width": 2
                                }}
                            }},
                            {{
                                "id": "tilecraft-points",
                                "type": "circle",
                                "source": "tilecraft",
                                "source-layer": "{source_layer}",
                                "filter": ["==", ["geometry-type"], "Point"],
                                "paint": {{
                                    "circle-color": "#ff6b6b",
                                    "circle-radius": 4,
                                    "circle-stroke-color": "#ffffff",
                                    "circle-stroke-width": 1
                                }}
                            }},
                            {{
                                "id": "tilecraft-polygons",
                                "type": "fill",
                                "source": "tilecraft",
                                "source-layer": "{source_layer}",
                                "filter": ["in", ["geometry-type"], ["literal", ["Polygon", "MultiPolygon"]]],
                                "paint": {{
                                    "fill-color": "#4ecdc4",
                                    "fill-opacity": 0.3
                                }}
                            }}
                        ]
                    }};
                    
                    map.setStyle(basicStyle);
                    updateServerStatus('✅ Tileserver-gl-light connected (basic style)');
                    customStyleLoaded = true;
                    
                    // Center map on the actual data bounds
                    map.fitBounds([
                        [{bbox.west}, {bbox.south}],
                        [{bbox.east}, {bbox.north}]
                    ], {{
                        padding: 50,
                        duration: 1000
                    }});
                }}
            }} catch (error) {{
                console.log('Tileserver-gl-light not available:', error);
            }}
        }}

        function updateServerStatus(message) {{
            const statusEl = document.getElementById('server-status');
            statusEl.className = 'server-status server-online';
            statusEl.innerHTML = message;
        }}

        // Check for tileserver every 3 seconds
        setInterval(loadTileserverStyle, 3000);
        
        // Add bounding box visualization
        map.on('load', () => {{
            map.addSource('bbox', {{
                'type': 'geojson',
                'data': {{
                    'type': 'Feature',
                    'geometry': {{
                        'type': 'Polygon',
                        'coordinates': [[
                            [{bbox.west}, {bbox.south}],
                            [{bbox.east}, {bbox.south}],
                            [{bbox.east}, {bbox.north}],
                            [{bbox.west}, {bbox.north}],
                            [{bbox.west}, {bbox.south}]
                        ]]
                    }}
                }}
            }});
            
            map.addLayer({{
                'id': 'bbox-outline',
                'type': 'line',
                'source': 'bbox',
                'paint': {{
                    'line-color': '#ff0000',
                    'line-width': 2,
                    'line-dasharray': [2, 2]
                }}
            }});
            
            // Try to load custom style immediately
            loadTileserverStyle();
        }});

        // Toggle info panel
        document.getElementById('toggle-info').addEventListener('click', function() {{
            const info = document.querySelector('.info');
            const btn = this;
            if (info.style.display === 'none') {{
                info.style.display = 'block';
                btn.textContent = 'Hide Info';
            }} else {{
                info.style.display = 'none';
                btn.textContent = 'Show Info';
            }}
        }});

        console.log('Tilecraft Preview initialized');
        console.log('Dataset:', '{tileset_name}');
        console.log('Center:', [{center_lng}, {center_lat}]);
        console.log('Zoom:', {zoom});
    </script>
</body>
</html>"""

    def _create_html_template(
        self, mbtiles_path: Path, style_path: Path, bbox: BoundingBox
    ) -> str:
        """Create HTML template for preview."""
        center_lng = (bbox.west + bbox.east) / 2
        center_lat = (bbox.south + bbox.north) / 2
        
        # Calculate appropriate zoom level based on bbox size
        lng_diff = abs(bbox.east - bbox.west)
        lat_diff = abs(bbox.north - bbox.south)
        max_diff = max(lng_diff, lat_diff)
        
        # Rough zoom calculation
        if max_diff > 10:
            zoom = 5
        elif max_diff > 1:
            zoom = 8
        elif max_diff > 0.1:
            zoom = 11
        else:
            zoom = 14

        return f"""<!DOCTYPE html>
<html>
<head>
    <title>Tilecraft Preview</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://unpkg.com/maplibre-gl@4.4.1/dist/maplibre-gl.js"></script>
    <link href="https://unpkg.com/maplibre-gl@4.4.1/dist/maplibre-gl.css" rel="stylesheet">
    <style>
        body {{ margin: 0; padding: 0; font-family: Arial, sans-serif; }}
        #map {{ position: absolute; top: 0; bottom: 0; width: 100%; }}
        .info {{
            position: absolute;
            top: 10px;
            left: 10px;
            background: rgba(255,255,255,0.95);
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            max-width: 300px;
            z-index: 1000;
        }}
        .info h3 {{ margin: 0 0 10px 0; color: #333; }}
        .info p {{ margin: 5px 0; font-size: 14px; color: #666; }}
        .server-status {{ padding: 8px; border-radius: 4px; margin-top: 10px; }}
        .server-offline {{ background: #ffebee; color: #c62828; }}
        .server-online {{ background: #e8f5e8; color: #2e7d32; }}
        .instructions {{ margin-top: 10px; font-size: 12px; }}
        .instructions code {{ background: #f5f5f5; padding: 2px 4px; border-radius: 3px; }}
    </style>
</head>
<body>
    <div id="map"></div>
    <div class="info">
        <h3>🗺️ Tilecraft Preview</h3>
        <p><strong>MBTiles:</strong> {mbtiles_path.name}</p>
        <p><strong>Style:</strong> {style_path.name}</p>
        <p><strong>Bounds:</strong> {bbox.west:.3f}, {bbox.south:.3f}, {bbox.east:.3f}, {bbox.north:.3f}</p>
        
        <div id="server-status" class="server-status server-offline">
            ⚠️ Tile server offline
        </div>
        
        <div class="instructions">
            <strong>To view tiles:</strong><br>
            1. Run: <code>python start_tile_server.py</code><br>
            2. Open: <code>http://localhost:8080</code>
        </div>
    </div>

    <script>
        // Initialize MapLibre GL
        const map = new maplibregl.Map({{
            container: 'map',
            style: {{
                "version": 8,
                "sources": {{
                    "raster-tiles": {{
                        "type": "raster",
                        "tiles": ["https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png"],
                        "tileSize": 256,
                        "attribution": "© OpenStreetMap contributors"
                    }}
                }},
                "layers": [{{
                    "id": "background",
                    "type": "raster",
                    "source": "raster-tiles"
                }}]
            }},
            center: [{center_lng}, {center_lat}],
            zoom: {zoom}
        }});

        map.addControl(new maplibregl.NavigationControl());
        map.addControl(new maplibregl.ScaleControl());

        // Try to load custom style when available
        async function loadCustomStyle() {{
            try {{
                const response = await fetch('/style.json');
                if (response.ok) {{
                    const style = await response.json();
                    map.setStyle(style);
                    document.getElementById('server-status').className = 'server-status server-online';
                    document.getElementById('server-status').innerHTML = '✅ Tile server running';
                }} else {{
                    console.log('Custom style not available, using fallback');
                }}
            }} catch (error) {{
                console.log('Failed to load custom style:', error);
            }}
        }}

        // Check for tile server every 2 seconds
        setInterval(loadCustomStyle, 2000);
        
        // Add bounding box visualization
        map.on('load', () => {{
            map.addSource('bbox', {{
                'type': 'geojson',
                'data': {{
                    'type': 'Feature',
                    'geometry': {{
                        'type': 'Polygon',
                        'coordinates': [[
                            [{bbox.west}, {bbox.south}],
                            [{bbox.east}, {bbox.south}],
                            [{bbox.east}, {bbox.north}],
                            [{bbox.west}, {bbox.north}],
                            [{bbox.west}, {bbox.south}]
                        ]]
                    }}
                }}
            }});
            
            map.addLayer({{
                'id': 'bbox-outline',
                'type': 'line',
                'source': 'bbox',
                'paint': {{
                    'line-color': '#ff0000',
                    'line-width': 2,
                    'line-dasharray': [2, 2]
                }}
            }});
        }});

        console.log('Tilecraft Preview initialized');
        console.log('MBTiles:', '{mbtiles_path}');
        console.log('Style:', '{style_path}');
        console.log('Center:', [{center_lng}, {center_lat}]);
        console.log('Zoom:', {zoom});
    </script>
</body>
</html>"""
