# Product Requirements Document (PRD)

## Project Title:

**AI-Assisted CLI Tool for Vector Tile Generation from OSM**

## Overview:

This project delivers a command-line interface (CLI) tool that ingests OpenStreetMap (OSM) data for a specified bounding box and set of natural features (e.g., rivers, forests, lakes), processes it, and outputs both Mapbox Vector Tiles (MBTiles) and a MapLibre GL JS-compatible style JSON file. The tool will use AI to assist in schema generation, style design, and pipeline orchestration.

## Target Users:

* GIS analysts and cartographers seeking lightweight, aesthetic tile generation
* Environmental nonprofits and researchers needing quick map outputs
* Web developers and designers exploring custom map styles

## Key Features:

1. **Bounding Box Input**
2. **Feature Type Selection**
3. **OSM Data Download & Clipping**
4. **Feature Extraction**
5. **GeoJSON Layer Generation**
6. **Vector Tile Generation (Tippecanoe)**
7. **Style JSON Generation (MapLibre GL JS)**
8. **Local Tile Server Preview** (Optional)
9. **Structured Output Directory**
10. **Caching and Intermediate Storage**
11. **Tag Disambiguation using AI**
12. **Validation and Preview Step**

---

## Workflow Breakdown

### 1. CLI Input Parameters

```bash
$ vector-cli --bbox "-109.2,36.8,-106.8,38.5" --features "rivers,forest,water" --palette "subalpine dusk"
```

### 2. AI-Assisted Schema + Style

* AI generates tile schema based on selected features
* AI generates MapLibre GL JS style JSON based on selected palette mood (e.g., "subalpine dusk")
* AI interprets and suggests fuzzy tag matching from OSM tag inconsistencies (e.g., `natural=wood` vs `landuse=forest`)

### 3. OSM Data Acquisition

* Download bounding region from Geofabrik or extract from full-state PBF
* Clip using `osmium` and `.poly` or bounding box
* Implements caching strategy for downloaded extracts

### 4. Feature Extraction

* Use `osmfilter` or `osmium tags-filter`
* Filter tags such as `natural=water`, `waterway=river`, `landuse=forest`
* Output thematic GeoJSON files for Tippecanoe
* Applies AI-aided tag disambiguation logic where applicable

### 5. Tile Generation

* Use `tippecanoe` to generate MBTiles
* Zoom-specific tuning based on feature type
* Streams or chunks large bounding boxes to manage performance and memory

### 6. Style Generation

* AI creates a MapLibre style JSON
* Includes sources, layers, paint rules, typography
* Ensures accessibility and contrast validation in style generation
* Style file saved alongside MBTiles

### 7. Validation & Preview

* Optional step for visual inspection of generated tiles and styles
* Generates static thumbnails or interactive HTML preview using MapLibre GL JS

### 8. Output

```
output/
├── tiles/
│   └── southwest.mbtiles
├── styles/
│   └── southwest-style.json
├── data/
│   ├── rivers.geojson
│   ├── forests.geojson
│   └── waterbodies.geojson
├── cache/
│   ├── raw.osm.pbf
│   └── extracted.poly
└── README.md
```

---

## Technical Stack

* **Language**: Python or Node.js (TBD)
* **OSM Tools**: `osmium`, `osmconvert`, `osmfilter`
* **Vector Tiling**: `tippecanoe`
* **Styling**: AI-assisted style prompt + MapLibre GL JS
* **Optional Services**: Dockerized Tileserver GL for preview
* **Caching**: Filesystem caching of PBF and intermediate GeoJSONs

---

## AI Integration Strategy

* Prompt-engineered schema builder from feature types
* Style generator based on palette mood and layer context
* Fuzzy tag matcher for interpreting OSM inconsistencies
* AI-assisted validation layer for style accessibility and cartographic clarity
* Optional: error handling and CLI feedback from AI agent

---

## Future Enhancements

* Upload MBTiles to S3/CDN
* Add elevation contours from external DEMs
* Enable overpass API instead of full PBF
* Add GUI for non-CLI users
* Multi-region streaming and distributed tile processing for large-scale rendering

---

## Prompt Library (for AI Calls)

### Schema Prompt

> “Generate a vector tile schema for the following OSM feature types: rivers, forest, waterbodies. Include geometry type, suggested attributes, and recommended minzoom/maxzoom levels.”

### Style Prompt

> “Generate a MapLibre GL JS style JSON for vector tiles representing rivers, lakes, and forests in Southwest Colorado using a 'subalpine dusk' palette. Rivers should glow cyan, lakes should be deep indigo, and forests muted jade. Use minimalist sans-serif typography and reduce label clutter. Ensure style contrast is accessible.”

### Tag Clarification Prompt

> “Given the feature type 'forest', identify all relevant OSM tags including synonyms, regional variants, and common misspellings or overlaps (e.g., `natural=wood`, `landuse=forest`, `leisure=nature_reserve`).”

---

## Acceptance Criteria

* CLI tool runs with bounding box + features + style palette as input
* Generates MBTiles and style JSON in < 5 minutes for a typical bounding box (with larger region fallback options)
* Resulting MapLibre style renders correctly and uses appropriate zoom logic
* Output files are logically organized, portable, and reproducible
* Caching is implemented for reuse and faster iterations
* Includes README with usage instructions and system requirements
* Preview step confirms style functionality and tile integrity

---

## Project Leads

* AI Design Agent: ChatGPT / Claude
* GIS Logic & Tiling: Richard (Human Geospatial Architect)

> "Design is not just what it looks like and feels like. Design is how it works." – Steve Jobs
