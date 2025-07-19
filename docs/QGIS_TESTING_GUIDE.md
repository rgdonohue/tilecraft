# 🗺️ QGIS Testing Guide for Tilecraft

This guide shows how to test Tilecraft's vector tile output in QGIS and other GIS applications.

## 📋 Real Output Summary

**Generated from Colorado region** (`-106.81,37.36,-104.49,38.39`):
- **MBTiles file**: `tileset.mbtiles` (56 MB)
- **Total tiles**: 7,912 vector tiles
- **Zoom levels**: 0-14 (pyramid structure)
- **Layers**: 3 layers (rivers, forest, water)
- **Features**: 130,546 total features
  - Rivers: 123,726 features (LineString)
  - Forest: 968 features (Polygon) 
  - Water: 5,852 features (Polygon)

## 🚀 Testing in QGIS

### Method 1: Direct MBTiles Loading

1. **Open QGIS** (version 3.16+ recommended)

2. **Add MBTiles Layer**:
   ```
   Layer → Add Layer → Add Vector Tile Layer
   ```

3. **Configure Connection**:
   - **Type**: File
   - **File**: Browse to `output/tiles/tileset.mbtiles`
   - **Name**: Tilecraft Output
   - Click **OK**

4. **Expected Result**:
   - Layer loads in QGIS with all zoom levels
   - Pan/zoom shows progressive detail
   - Layer panel shows 3 sublayers: rivers, forest, water

### Method 2: HTTP Server Testing

For web-based testing (simulates production deployment):

1. **Start Local Server**:
   ```bash
   cd output/tiles
   python3 -m http.server 8000
   ```

2. **Create MBTiles Server URL**:
   ```
   http://localhost:8000/tileset.mbtiles
   ```

3. **Add in QGIS**:
   - Layer → Add Vector Tile Layer
   - Type: HTTP/HTTPS/FTP
   - URL: `http://localhost:8000/tileset.mbtiles`

## 🔍 Validation Checklist

### ✅ Basic Functionality
- [ ] **Layer loads without errors**
- [ ] **All 3 layers visible** (rivers, forest, water)
- [ ] **Zoom levels 0-14 work** (test pan/zoom)
- [ ] **Features render correctly** at different zoom levels

### ✅ Data Quality
- [ ] **River networks connected** (no broken segments)
- [ ] **Forest areas filled properly** (polygon rendering)
- [ ] **Water bodies accurate** (lakes, reservoirs visible)
- [ ] **Geographic accuracy** (features align with base maps)

### ✅ Performance
- [ ] **Smooth zoom/pan** (no lag)
- [ ] **Quick layer switching** (layers toggle fast)
- [ ] **Memory usage reasonable** (check QGIS memory)
- [ ] **File size appropriate** (56MB for 130k+ features)

### ✅ Metadata Validation
- [ ] **Projection correct** (WGS84/Web Mercator)
- [ ] **Bounds accurate** (Colorado region)
- [ ] **Attribute data present** (names, types, OSM IDs)

## 🗂️ Alternative Testing Tools

### 1. **MapProxy/TileServer**
```bash
# Install tileserver-gl
npm install -g @maplibre/tileserver-gl

# Serve tiles
tileserver-gl output/tiles/tileset.mbtiles
```
Access: `http://localhost:8080`

### 2. **MapLibre GL JS** (Web Browser)
```html
<!DOCTYPE html>
<html>
<head>
    <script src='https://unpkg.com/maplibre-gl@2.4.0/dist/maplibre-gl.js'></script>
    <link href='https://unpkg.com/maplibre-gl@2.4.0/dist/maplibre-gl.css' rel='stylesheet' />
</head>
<body>
    <div id='map' style='width: 100%; height: 100vh;'></div>
    <script>
        const map = new maplibregl.Map({
            container: 'map',
            center: [-105.5, 37.8],
            zoom: 8,
            style: {
                version: 8,
                sources: {
                    tilecraft: {
                        type: 'vector',
                        url: 'mbtiles://./tileset.mbtiles'
                    }
                },
                layers: [
                    {
                        id: 'rivers',
                        source: 'tilecraft',
                        'source-layer': 'rivers',
                        type: 'line',
                        paint: { 'line-color': '#4A90E2', 'line-width': 2 }
                    },
                    {
                        id: 'forest',
                        source: 'tilecraft',
                        'source-layer': 'forest',
                        type: 'fill',
                        paint: { 'fill-color': '#228B22', 'fill-opacity': 0.7 }
                    },
                    {
                        id: 'water',
                        source: 'tilecraft',
                        'source-layer': 'water',
                        type: 'fill',
                        paint: { 'fill-color': '#1E90FF', 'fill-opacity': 0.8 }
                    }
                ]
            }
        });
    </script>
</body>
</html>
```

### 3. **Command Line Inspection**
```bash
# Tile inspection with tippecanoe tools
tippecanoe-decode output/tiles/tileset.mbtiles 8 51 99 | head -20

# SQLite inspection
sqlite3 output/tiles/tileset.mbtiles
.schema
SELECT COUNT(*) FROM map;
SELECT zoom_level, COUNT(*) FROM map GROUP BY zoom_level;
```

## 📊 Expected Performance Metrics

### Tile Distribution (Zoom 0-14)
```
Zoom  0: 1 tile     (world overview)
Zoom  1: 2 tiles    (continental)
Zoom  8: 6 tiles    (regional)
Zoom 10: 45 tiles   (local)
Zoom 14: 5,659 tiles (detailed)
```

### Feature Density by Layer
- **Rivers**: High density (123k+ features) - detailed drainage network
- **Forest**: Medium density (968 features) - major forest areas
- **Water**: Medium density (5.8k features) - lakes, reservoirs, ponds

### File Characteristics
- **Format**: SQLite with new schema (map + images tables)
- **Compression**: PBF (Protocol Buffer) format
- **Encoding**: UTF-8 with full attribute preservation
- **Bounds**: Colorado region (-106.81° to -104.49° lon, 37.36° to 38.39° lat)

## 🚨 Common Issues & Solutions

### **Issue**: "MBTiles file not recognized"
**Solution**: Ensure QGIS 3.16+ and enable Vector Tiles plugin

### **Issue**: "Empty or corrupt tiles"
**Solution**: Verify file integrity:
```bash
sqlite3 output/tiles/tileset.mbtiles "SELECT COUNT(*) FROM map;"
```

### **Issue**: "Rendering performance slow"
**Solution**: Check QGIS settings:
- Enable GPU acceleration
- Increase cache size (Settings → Options → Rendering)

### **Issue**: "Missing attribution data"
**Solution**: Verify metadata:
```bash
sqlite3 output/tiles/tileset.mbtiles "SELECT * FROM metadata WHERE name='attribution';"
```

## 🎯 Production Deployment Testing

### 1. **Web Server Configuration**
- Test with Apache/Nginx serving MBTiles
- Verify CORS headers for web applications
- Check gzip compression for .mbtiles files

### 2. **CDN Integration**
- Upload to S3/CloudFront for global distribution
- Test edge caching behavior
- Monitor bandwidth usage

### 3. **Mobile Testing**
- Test with Mapbox Mobile SDKs
- Verify offline capabilities
- Check memory usage on devices

## 📈 Quality Assurance Workflow

1. **Automated Validation**:
   ```bash
   # Run Tilecraft tile generator tests
   pytest tests/test_tile_generator.py -v
   
   # Validate MBTiles structure
   python -c "
   import sqlite3
   conn = sqlite3.connect('output/tiles/tileset.mbtiles')
   tables = conn.execute('SELECT name FROM sqlite_master WHERE type=\"table\"').fetchall()
   print('Tables:', [t[0] for t in tables])
   print('Tile count:', conn.execute('SELECT COUNT(*) FROM map').fetchone()[0])
   "
   ```

2. **Visual Inspection**:
   - Load in QGIS and compare with OSM base layer
   - Check feature alignment and completeness
   - Verify styling renders correctly

3. **Performance Testing**:
   - Measure load times at different zoom levels
   - Test concurrent user access
   - Monitor server resource usage

---

This comprehensive testing approach ensures Tilecraft's vector tile output is production-ready and performs well across different GIS platforms and use cases.