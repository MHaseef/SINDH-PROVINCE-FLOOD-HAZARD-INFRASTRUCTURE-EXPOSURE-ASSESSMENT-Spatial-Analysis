# Sindh Flood Response & Infrastructure Exposure Analysis
### Vector-based Multi-Criteria Spatial Analysis & Emergency Decision Support for PDMA Sindh

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![GeoPandas](https://img.shields.io/badge/GeoPandas-1.1.4-green?style=for-the-badge&logo=pandas&logoColor=white)
![QGIS](https://img.shields.io/badge/QGIS-3.x-589632?style=for-the-badge&logo=qgis&logoColor=white)
![CRS](https://img.shields.io/badge/EPSG-32642%20(UTM%20Zone%2042N)-orange?style=for-the-badge)
![Datastore](https://img.shields.io/badge/Datastore-OGC%20GeoPackage-003366?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Completed-brightgreen?style=for-the-badge)

---

## 📌 Executive Summary

During catastrophic monsoon flooding along the lower Indus River basin in **Sindh, Pakistan**, rising floodwaters frequently submerge critical transport networks, inundate emergency health centers, and sever vital lifelines for rural communities. To enable the **Provincial Disaster Management Authority (PDMA) Sindh** to deploy targeted disaster relief and allocate resources effectively, this project delivers a rigorous, vector-based multi-criteria spatial analysis workflow.

By standardizing spatial layers into a projected Cartesian coordinate system (**UTM Zone 42N / EPSG:32642**), executing multi-ring hydrological hazard buffering, performing spatial overlay intersections, and computing nearest-neighbor distance matrices via spatial KD-Trees, this system quantifies:
1. **Transportation Network Vulnerability:** Exact kilometers of primary arterial highways submerged across flood hazard zones.
2. **Healthcare Infrastructure Exposure:** The proportion and count of medical centers directly inundated or rendered inaccessible.
3. **Community Isolation Impact:** The net straight-line distance increase experienced by local settlement populations to reach operational (unflooded) healthcare facilities.

---

## 🛠️ Software Toolchain & Technical Specifications

| Technology Category | Software / Library | Functional Role & Technical Usage |
| :--- | :--- | :--- |
| **Programming & Analytics** | **Python 3.10+** | Core execution environment for automated geospatial pipelines. |
| **Vector Engine** | **GeoPandas (`gpd`)** | Spatial dataframe engine handling spatial joins, overlays, coordinate transformations, and GeoPackage I/O. |
| **Spatial Geometry** | **Shapely** | Planar geometry construct engine for fast multi-ring buffering (`union_all()`) and geometric metric calculations. |
| **Distance Matrix Processing** | **SciPy (`scipy.spatial.KDTree`)** | Fast $O(N \log M)$ nearest-neighbor spatial tree algorithm computing Euclidean distance matrices between 7,900+ settlements and health facilities. |
| **Data Science Libraries** | **Pandas & NumPy** | High-performance tabular data aggregation, numerical indexing, and CSV report export. |
| **Desktop GIS & Cartography** | **QGIS 3.x** | Print Layout Engine, Jenks Natural Breaks choropleth rendering, symbology design, and map layout generation. |
| **Data Acquisition** | **Overpass API (OSM) & HDX** | Programmatic REST extraction of OpenStreetMap highways, settlements, health facilities, river channels, and HDX Tehsil boundaries. |
| **Spatial Reference System** | **EPSG:32642 (UTM Zone 42N)** | Conformal metric projection enabling true planar meter ($m$) and square kilometer ($\text{km}^2$) computations across Sindh. |

---

## 📐 Methodology & Workflow Architecture

```
+----------------------------------------------------------------------------------------------------------------+
|                                    GIS 402 - SPATIAL DATA ANALYSIS WORKFLOW                                    |
+----------------------------------------------------------------------------------------------------------------+
|                                                                                                                |
|  [ Module 1: Acquisition & Standardization ]                                                                   |
|  - HDX Boundary File -> Filter 'ADM1_EN' == 'Sindh' (125 Tehsils)                                              |
|  - Overpass Turbo API -> Roads (10,259), Health Points (1,732), Settlements (7,923), Indus River (1,073)       |
|  - Reproject EPSG:4326 -> EPSG:32642 | Store in 'Sindh_Flood_Analysis.gpkg'                                    |
|                                         |                                                                      |
|                                         v                                                                      |
|  [ Module 2: Attribute Queries & Metric Computation ]                                                         |
|  - Calculate Polygon Area -> Tehsil_SqKm = Area_m2 / 1,000,000                                                 |
|  - Filter High-Capacity Arterial Highways -> "highway" IN ('trunk','primary') & "surface" NOT IN ('dirt')      |
|  - Classify Health Infrastructure -> Hospitals, Clinics, BHUs, DHQs                                            |
|                                         |                                                                      |
|                                         v                                                                      |
|  [ Module 3: Proximity Analysis & Spatial Overlays ]                                                           |
|  - Multi-Ring Buffering -> High (1 km), Moderate (3 km), Extended (5 km)                                       |
|  - Spatial Intersection Overlay -> gpd.overlay(arterial_roads, buffer_3km) -> Submerged Roads (2,600.06 km)     |
|  - Point-in-Polygon Join -> Count health facilities per Tehsil -> Health_Count                                 |
|                                         |                                                                      |
|                                         v                                                                      |
|  [ Module 4: Accessibility & Distance Matrix Analysis ]                                                        |
|  - Health Invalidation -> Filter unflooded health facilities outside 3 km buffer -> active_health_centers       |
|  - cKDTree Spatial Query -> Compute baseline vs. inundated travel distances for 7,923 settlements              |
|  - Isolation Impact -> Distance_Increase_Km = Inundated_Dist_Km - Baseline_Dist_Km                             |
|                                                                                                                |
+----------------------------------------------------------------------------------------------------------------+
```

### Module Breakdown

#### 1. Module 1: Spatial Data Acquisition & Layer Standardization
- **Administrative Boundaries:** National Tehsil boundary dataset (`pak_admin3.shp`) filtered for Sindh Province (`ADM1_EN == 'Sindh'`), extracting **125 Tehsil polygons**.
- **OpenStreetMap Data Mining:** Programmatically queried the Overpass API endpoint using a custom HTTP header (`SDALab1_GIS402_FloodAnalysis/1.0`) to extract roads, healthcare points, population settlements, and the Indus River mainstem channel.
- **Reprojection & Datastore Initialization:** Reprojected all 5 raw vector layers from spherical geographic coordinates (`EPSG:4326`) to projected metric coordinates (**`EPSG:32642`**). Saved layers into an OGC GeoPackage container: `Sindh_Flood_Analysis.gpkg`.

#### 2. Module 2: Attribute Querying & Metric Calculation
- **Tehsil Land Area:** Computed planar polygon area for each Tehsil in square kilometers ($\text{Tehsil\_SqKm} = \text{Area}_{m^2} / 1,000,000.0$). Total analyzed Sindh land area: **140,948.39 km²**.
- **Arterial Highway Isolation:** Executed SQL attribute expressions (`"highway" IN ('trunk', 'primary') AND "surface" NOT IN ('unpaved', 'dirt')`) to isolate high-speed paved highways (**4,912 segments**, totaling **9,365.92 km**).
- **Health Center Classification:** Filtered functional District Headquarter (DHQ) hospitals, Basic Health Units (BHUs), and primary clinics (**1,732 point features**).

#### 3. Module 3: Hydrological Hazard Buffering & Spatial Overlays
- **Multi-Ring Hazard Bands:** Generated 3 continuous dissolved buffer rings around the Indus River mainstem (`indus_river`):
  - **High Hazard Zone:** 1,000 m (1 km) buffer (`indus_buffer_1km`)
  - **Moderate Hazard Zone:** 3,000 m (3 km) buffer (`indus_buffer_3km`)
  - **Extended Risk Zone:** 5,000 m (5 km) buffer (`indus_buffer_5km`)
- **Inundated Highway Overlay:** Executed spatial intersection overlay (`gpd.overlay(how='intersection')`) between `sindh_arterial_roads` and `indus_buffer_3km`. Calculated exact submerged segment lengths in kilometers (`Segment_Length_Km`).
- **Point-in-Polygon Aggregation:** Spatial join mapping healthcare point facilities to Tehsil polygons to populate the **`Health_Count`** attribute field.

#### 4. Module 4: Accessibility & Distance Matrix Analysis
- **Operational Health Center Invalidation:** Identified healthcare points inside the 3 km flood zone (**1,152 facilities / 66.51% inundated**), isolating the remaining **580 active/unflooded health centers** into `active_health_centers`.
- **Fast Nearest-Neighbor Spatial Distance Matrix:** Implemented SciPy `cKDTree` algorithm between **7,923 settlement centroids** and health centers to calculate:
  - `Baseline_Dist_Km`: Straight-line distance to nearest health facility prior to flood.
  - `Inundated_Dist_Km`: Straight-line distance to nearest *operational* health facility during flood.
  - `Distance_Increase_Km`: Net travel distance increase quantifying community isolation.

---

## 📊 Key Analytical Findings & Metrics

### 1. Transportation Infrastructure Exposure Summary

| Exposure Metric | Quantitative Result |
| :--- | :--- |
| **Total Arterial Highway Inundated (3 km Buffer)** | **2,600.06 km** |
| **Total Submerged Road Segments** | **2,502 segments** |
| **Proportion of Total Arterial Network Submerged** | **27.76%** |
| **Most Impacted Tehsil** | **Bin Qasim Town** (*Malir Karachi District*) |
| **Highest Tehsil Inundated Highway Length** | **147.91 km** |

### 2. Healthcare Facility Exposure Breakdown

| Flood Hazard Zone | Buffer Radius | Facilities Exposed | Inundation Percentage (%) |
| :--- | :---: | :---: | :---: |
| **High Hazard Zone** | 1,000 m (1 km) | **293** | **16.92%** |
| **Moderate Hazard Zone** | 3,000 m (3 km) | **1,152** | **66.51%** |
| **Extended Risk Zone** | 5,000 m (5 km) | **1,418** | **81.87%** |
| **Operational (Unflooded) Health Centers** | > 3,000 m | **580** | **33.49%** |

### 3. Top 3 Most Isolated Settlement Population Centers

```
1. Wasan (Village)
   ├── Baseline Distance to Medical Care:    1.16 km
   ├── Flood Scenario Distance to Care:     49.97 km
   └── Net Isolation Increase:             +48.81 km (Nearest Active Center: RHC Kandhra)

2. Ranipur / رانی پور (Town)
   ├── Baseline Distance to Medical Care:    0.52 km
   ├── Flood Scenario Distance to Care:     48.40 km
   └── Net Isolation Increase:             +47.88 km (Nearest Active Center: RHC Kandhra)

3. Goth Machhi (Village)
   ├── Baseline Distance to Medical Care:    2.31 km
   ├── Flood Scenario Distance to Care:     50.06 km
   └── Net Isolation Increase:             +47.75 km (Nearest Active Center: BHU MARO DERA)
```

---

## 🌐 Coordinate Reference System (CRS) Technical Justification

A critical requirement of spatial data analysis is selecting an appropriate Coordinate Reference System (CRS). Global vector repositories provide vector features in **WGS 84 / `EPSG:4326`** (Geographic Coordinate System). However, performing buffer operations, line length calculations, or polygon area calculations directly in `EPSG:4326` yields invalid results.

```
+----------------------------------------------------------------------------------------------------+
|                                    GEOGRAPHIC VS. PROJECTED CRS                                    |
+----------------------------------------------------------------------------------------------------+
|  EPSG:4326 (WGS 84 - Geographic)             |  EPSG:32642 (UTM Zone 42N - Projected Cartesian)     |
|  - Coordinate Units: Angular Degrees (°)     |  - Coordinate Units: Linear Meters (m)              |
|  - Distance varies with Latitude (cos φ)     |  - Constant, isotropic scale grid                   |
|  - Area output: deg² (meaningless metric)    |  - Area output: m² -> Converted to km²              |
|  - Buffers distort into squished ellipses    |  - Buffers form true, exact isometric circles       |
+----------------------------------------------------------------------------------------------------+
```

### Mathematical & Distortion Principles:
1. **Meridian Convergence:** In `EPSG:4326`, coordinate units are expressed in angular degrees ($\text{latitude}, \text{longitude}$). While 1 degree of latitude is relatively constant (~111 km), 1 degree of longitude shrinks as a function of latitude ($\text{Length} \approx 111.32 \times \cos(\text{latitude})$ km). At Sindh's average latitude (~25°N), $1^\circ$ longitude is only ~100.8 km.
2. **Buffer Distortion:** Generating a 3,000-meter buffer in `EPSG:4326` requires converting meters into degrees. Because $1^\circ$ lat $\neq 1^\circ$ lon, the resulting buffer ring becomes a distorted ellipse rather than a true circle.
3. **Planar Metric Integrity in `EPSG:32642`:** Universal Transverse Mercator (UTM) Zone 42N is a conformal Cartesian projection spanning 66°E to 72°E, specifically designed for Pakistan. Its grid units are strictly in **meters ($m$)**, ensuring true distance preservation, isotropic buffering, and precise metric area ($\text{km}^2$) and length ($\text{km}$) computations.

---

### Layer Inventory inside `Sindh_Flood_Analysis.gpkg`

| Layer Name | Geometry | Features | Projection | Description / Key Attributes |
| :--- | :--- | :---: | :---: | :--- |
| `sindh_tehsils` | MultiPolygon | 125 | `EPSG:32642` | Administrative boundaries with `Tehsil_SqKm` and `Health_Count` |
| `sindh_roads` | LineString | 10,259 | `EPSG:32642` | Raw OpenStreetMap highway infrastructure |
| `sindh_arterial_roads` | LineString | 4,912 | `EPSG:32642` | High-capacity paved highways with `Length_Km` metric |
| `sindh_health_facilities` | Point | 1,732 | `EPSG:32642` | Active healthcare facilities (Hospitals, Clinics, BHUs, DHQs) |
| `sindh_settlements` | Point | 7,923 | `EPSG:32642` | Population centers with baseline vs inundated travel distance metrics |
| `indus_river` | LineString | 1,073 | `EPSG:32642` | Indus River mainstem channel segments |
| `indus_buffer_1km` | Polygon | 1 | `EPSG:32642` | High Hazard Zone (1,000 m buffer) |
| `indus_buffer_3km` | Polygon | 1 | `EPSG:32642` | Moderate Hazard Zone (3,000 m buffer) |
| `indus_buffer_5km` | Polygon | 1 | `EPSG:32642` | Extended Risk Zone (5,000 m buffer) |
| `indus_river_buffers` | Polygon | 3 | `EPSG:32642` | Multi-ring combined buffer hazard layer |
| `inundated_arterial_roads` | LineString | 2,502 | `EPSG:32642` | Highways submerged within 3 km flood zone (`Segment_Length_Km`) |
| `active_health_centers` | Point | 580 | `EPSG:32642` | Unflooded operational health facilities outside 3 km buffer |

---

## ⚡ Execution Instructions

To execute the entire pipeline and generate all deliverables from scratch:

```bash
# 1. Activate Virtual Environment
.venv\Scripts\activate

# 2. Run Module 1: Vector Acquisition & Reprojection
python module1_data_pipeline.py

# 3. Run Module 2: Attribute Queries & Metric Computations
python module2_attribute_metrics.py

# 4. Run Module 3: Hydrological Buffering & Spatial Overlays
python module3_proximity_analysis.py

# 5. Run Module 4: Accessibility & Distance Matrix Computation
python module4_distance_matrix.py
```

---

## 📜 License & Citation
* **Course:** GIS 402 - Spatial Data Analysis
* **Study Area:** Sindh Province, Pakistan
* **Target Audience:** Provincial Disaster Management Authority (PDMA) Sindh & GIS Response Leads
