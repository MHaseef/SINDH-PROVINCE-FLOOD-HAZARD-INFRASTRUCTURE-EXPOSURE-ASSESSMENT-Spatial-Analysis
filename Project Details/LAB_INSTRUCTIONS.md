# SDA Lab 1: Vector Spatial Analysis for Flood Response & Infrastructure Exposure in Sindh, Pakistan
**Course:** GIS 402 - Spatial Data Analysis  
**Target CRS:** EPSG:32642 (WGS 84 / UTM Zone 42N)  
**Execution Strategy:** Option C — Hybrid Python Automation (Data Pipeline & Spatial Analytics) + QGIS Layout Designer (Cartography)

---

## 1. Operational Scenario & Objectives
During severe monsoon flooding along the lower Indus River basin in Sindh, transport networks and healthcare access are heavily disrupted. The Provincial Disaster Management Authority (PDMA) Sindh requires a vector-based GIS assessment to identify infrastructure at risk, evaluate health center exposure, and quantify community isolation metrics.

---

## 2. Lab Module Breakdown & Technical Requirements

### Module 1: Vector Acquisition & Layer Standardization
1. **Administrative Boundaries:**
   - Filter national Tehsil vector dataset (`pak_admbnda_adm3_30m.shp`) to isolate Sindh Province using SQL/Pandas expression:
     `"ADM1_EN" == 'Sindh'`
2. **Infrastructure & Health Data (Overpass Turbo API):**
   - Execute spatial query over Sindh / Indus corridor (`Dadu / Sukkur / Hyderabad` region) to extract:
     - High-capacity roads: `way["highway"~"trunk|primary|secondary"]`
     - Medical facilities: `node["amenity"~"hospital|clinic"]`
3. **Indus River & Settlements:**
   - Load mainstem river geometry (Line/Polygon) and settlement location centroids/polygons.
4. **Reprojection & Datastore Initialization:**
   - Reproject all raw vectors from `EPSG:4326` (WGS 84) to local metric projected coordinate system **`EPSG:32642` (UTM Zone 42N)**.
   - Store all standardized layers into a single GeoPackage container: `Sindh_Flood_Analysis.gpkg`.

---

### Module 2: Attribute Queries & Geometric Metric Computation
1. **Tehsil Area Calculation:**
   - Calculate area in square kilometers for each Tehsil polygon:
     $$\text{Tehsil\_SqKm} = \frac{\text{Area}_{m^2}}{1,000,000}$$
2. **Arterial Highway Isolation:**
   - Filter primary transportation infrastructure:
     `"highway" IN ('trunk', 'primary') AND "surface" NOT IN ('unpaved', 'dirt')`
3. **Health Facility Classification:**
   - Isolate active District Headquarter (DHQ) hospitals and Basic Health Units (BHUs) into dedicated point layer: `sindh_health_facilities`.

---

### Module 3: Proximity Analysis & Spatial Overlays
1. **Hydrological Multi-Ring Buffering:**
   - Generate multi-ring distance hazard buffers around the Indus River vector geometry:
     - **High Hazard Zone:** 1,000 meters (1 km)
     - **Moderate Hazard Zone:** 3,000 meters (3 km)
     - **Extended Risk Zone:** 5,000 meters (5 km)
2. **Inundated Road Network Intersect:**
   - Execute spatial intersection (`gpd.overlay(how='intersection')`) between primary highways and the 3 km moderate hazard buffer.
   - Calculate exact impacted road length in kilometers:
     $$\text{Segment\_Length\_Km} = \frac{\text{Length}_{m}}{1,000}$$
3. **Point-in-Polygon Facility Aggregation:**
   - Count healthcare point facilities located within each Tehsil boundary and populate field: `Health_Count`.

---

### Module 4: Accessibility & Distance Matrix Analysis
1. **Identify Operational Facilities:**
   - Select healthcare facility points intersecting the 3 km flood zone.
   - Isolate unflooded/operational hospitals into layer: `active_health_centers`.
2. **Distance Matrix Computation:**
   - Compute Euclidean linear distance matrix (1 to nearest 1 target) between settlement centroids (origins) and `active_health_centers` (destinations).
   - Determine baseline vs. inundated scenario distance increases to quantify community isolation.

---

## 3. Analytical Questions & Reporting
1. **Road Infrastructure Vulnerability:** Total highway length (km) in 3 km flood buffer across Sindh, and identify the most impacted Tehsil.
2. **Healthcare Inaccessibility:** Count and percentage of health facilities directly inside the High Hazard Zone (1 km buffer).
3. **Community Isolation:** Identify top 3 settlement points facing the largest straight-line distance increase to active health centers.
4. **CRS Impact Reflection:** Technical justification explaining why calculations in `EPSG:4326` yield invalid area and length metrics compared to `EPSG:32642`.

---

## 4. Expected Deliverables Checklist
1. **`Sindh_Flood_Analysis.gpkg`**: Unified database with all projected vector layers (`EPSG:32642`).
2. **`GIS402_Lab1_Metrics_Summary.csv`**: Table summarizing inundated road lengths and health facility counts aggregated by Tehsil/District.
3. **Cartographic Map Output (A4 PDF)**: High-resolution map with choropleth health density, river hazard bands, road exposure, legend, scale bar, north arrow, and UTM grid.