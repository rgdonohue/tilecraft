# Tilecraft Preview

## Quick Start with tileserver-gl-light

### 1. Install tileserver-gl-light
```bash
npm install -g tileserver-gl-light
```

### 2. Start the server (Option A - Simple)
```bash
# Point directly at your mbtiles file or directory
tileserver-gl-light /Users/richard/Documents/projects/tilecraft/output/cache/89519c08a1ef5f10.mbtiles
```

### 2. Start the server (Option B - With config)
```bash
cd /Users/richard/Documents/projects/tilecraft/test-preview
tileserver-gl-light --config config.json
```

### 3. View your tiles
- Open http://localhost:8080 in your browser
- Select your dataset: `89519c08a1ef5f10`
- Or view directly at: http://localhost:8080/data/89519c08a1ef5f10/

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
