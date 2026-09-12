import os
import requests
import geopandas as gpd
from shapely.geometry import Point, LineString

# Define Target Coordinate Reference System (UTM Zone 42N for Sindh, Pakistan)
TARGET_CRS = "EPSG:32642"
GPKG_PATH = "Sindh_Flood_Analysis.gpkg"

print("====================================================================")
print("  SDA Lab 1 - Module 1: Data Acquisition & Standardization Pipeline ")
print("====================================================================")

# Bounding box for Sindh Province: [south, west, north, east]
bbox_sindh = "23.5,66.5,28.5,71.0"
headers = {'User-Agent': 'SDALab1_GIS402_FloodAnalysis/1.0 (spatial_data_analysis)'}

overpass_servers = [
    'https://overpass-api.de/api/interpreter',
    'https://overpass.kumi.systems/api/interpreter',
    'https://overpass.private.coffee/api/interpreter'
]

def query_overpass(ql_query):
    for server in overpass_servers:
        try:
            resp = requests.post(server, data={'data': ql_query}, headers=headers, timeout=60)
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            continue
    raise RuntimeError("Failed to query Overpass API from all endpoint servers.")

# -------------------------------------------------------------------
# 1. Process Tehsil Administrative Boundaries
# -------------------------------------------------------------------
print("\n[1/5] Processing Tehsil Administrative Boundaries...")

admin_shp_candidates = ["pak_admbnda_adm3_30m.shp", "pak_admin3.shp"]
admin_shp_path = None
for candidate in admin_shp_candidates:
    if os.path.exists(candidate):
        admin_shp_path = candidate
        break

if admin_shp_path:
    print(f"   -> Loading boundary shapefile: '{admin_shp_path}'")
    gdf_admin = gpd.read_file(admin_shp_path)
    
    # Normalize column names for consistency
    col_map = {}
    for col in gdf_admin.columns:
        col_lower = col.lower()
        if col_lower in ['adm1_en', 'adm1_name']:
            col_map[col] = 'ADM1_EN'
        elif col_lower in ['adm2_en', 'adm2_name']:
            col_map[col] = 'ADM2_EN'
        elif col_lower in ['adm3_en', 'adm3_name']:
            col_map[col] = 'ADM3_EN'
            
    gdf_admin = gdf_admin.rename(columns=col_map)
    
    # Filter for Sindh Province
    gdf_sindh_tehsils = gdf_admin[gdf_admin['ADM1_EN'].str.lower() == 'sindh'].copy()
    print(f"   -> Filtered {len(gdf_sindh_tehsils)} Tehsil boundaries for Sindh.")
else:
    raise FileNotFoundError("Could not find any Tehsil administrative shapefile (pak_admin3.shp or pak_admbnda_adm3_30m.shp).")

# -------------------------------------------------------------------
# 2. Fetch Roads & Healthcare Data via Overpass API
# -------------------------------------------------------------------
print("\n[2/5] Querying Overpass API for roads and health facilities in Sindh...")

infra_query = f"""
[out:json][timeout:90];
(
  way["highway"~"trunk|primary|secondary"]({bbox_sindh});
  node["amenity"~"hospital|clinic"]({bbox_sindh});
  way["amenity"~"hospital|clinic"]({bbox_sindh});
);
out center geom;
"""

data_infra = query_overpass(infra_query)

road_features = []
health_features = []

for elem in data_infra.get('elements', []):
    tags = elem.get('tags', {})
    
    # Health Facilities (Nodes or Ways with center)
    if 'amenity' in tags:
        if elem['type'] == 'node':
            lon, lat = elem['lon'], elem['lat']
        elif 'center' in elem:
            lon, lat = elem['center']['lon'], elem['center']['lat']
        else:
            continue
            
        health_features.append({
            'geometry': Point(lon, lat),
            'name': tags.get('name', 'Unknown Medical Center'),
            'amenity': tags.get('amenity'),
            'facility_type': tags.get('healthcare', tags.get('amenity')),
            'operator': tags.get('operator', 'Public/Private')
        })
        
    # Roads (Ways with geometry coordinates)
    elif elem['type'] == 'way' and 'highway' in tags:
        if 'geometry' in elem and len(elem['geometry']) >= 2:
            coords = [(pt['lon'], pt['lat']) for pt in elem['geometry']]
            road_features.append({
                'geometry': LineString(coords),
                'highway': tags.get('highway'),
                'ref': tags.get('ref', ''),
                'surface': tags.get('surface', 'paved'),
                'lanes': tags.get('lanes', '1')
            })

gdf_roads_raw = gpd.GeoDataFrame(road_features, crs="EPSG:4326") if road_features else gpd.GeoDataFrame()
gdf_health_raw = gpd.GeoDataFrame(health_features, crs="EPSG:4326") if health_features else gpd.GeoDataFrame()

print(f"   -> Retrieved {len(gdf_roads_raw)} road network segments.")
print(f"   -> Retrieved {len(gdf_health_raw)} health facility points.")

# -------------------------------------------------------------------
# 3. Fetch Settlements & Urban Centers (Required for Module 4)
# -------------------------------------------------------------------
print("\n[3/5] Querying Overpass API for Settlements & Urban Population Centers...")

settlements_query = f"""
[out:json][timeout:90];
(
  node["place"~"city|town|village|hamlet"]({bbox_sindh});
);
out center;
"""

data_settlements = query_overpass(settlements_query)

settlement_features = []
for elem in data_settlements.get('elements', []):
    tags = elem.get('tags', {})
    lon, lat = elem['lon'], elem['lat']
    settlement_features.append({
        'geometry': Point(lon, lat),
        'name': tags.get('name', 'Unnamed Settlement'),
        'place': tags.get('place'),
        'pop_est': int(tags.get('population', 0)) if tags.get('population', '').isdigit() else 0
    })

gdf_settlements_raw = gpd.GeoDataFrame(settlement_features, crs="EPSG:4326")
print(f"   -> Retrieved {len(gdf_settlements_raw)} settlement points across Sindh.")

# -------------------------------------------------------------------
# 4. Fetch Indus River Mainstem Geometry
# -------------------------------------------------------------------
print("\n[4/5] Fetching Indus River mainstem geometry from Overpass API...")

river_query = f"""
[out:json][timeout:90];
(
  way["waterway"="river"]({bbox_sindh});
);
out geom;
"""

data_river = query_overpass(river_query)

river_features = []
for elem in data_river.get('elements', []):
    if elem['type'] == 'way' and 'geometry' in elem and len(elem['geometry']) >= 2:
        coords = [(pt['lon'], pt['lat']) for pt in elem['geometry']]
        tags = elem.get('tags', {})
        name = tags.get('name', 'Indus River')
        river_features.append({
            'geometry': LineString(coords),
            'name': name,
            'waterway': 'river'
        })

gdf_river_raw = gpd.GeoDataFrame(river_features, crs="EPSG:4326") if river_features else gpd.GeoDataFrame()
print(f"   -> Retrieved {len(gdf_river_raw)} Indus River mainstem segments.")

# -------------------------------------------------------------------
# 5. Reproject to EPSG:32642 and Save to GeoPackage
# -------------------------------------------------------------------
print(f"\n[5/5] Reprojecting all layers to {TARGET_CRS} and saving into '{GPKG_PATH}'...")

gdf_sindh_tehsils_proj = gdf_sindh_tehsils.to_crs(TARGET_CRS)
gdf_roads_proj = gdf_roads_raw.to_crs(TARGET_CRS)
gdf_health_proj = gdf_health_raw.to_crs(TARGET_CRS)
gdf_settlements_proj = gdf_settlements_raw.to_crs(TARGET_CRS)
gdf_river_proj = gdf_river_raw.to_crs(TARGET_CRS)

# Save layers to GeoPackage datastore (using engine='pyogrio' or default to_file)
gdf_sindh_tehsils_proj.to_file(GPKG_PATH, layer="sindh_tehsils", driver="GPKG")
gdf_roads_proj.to_file(GPKG_PATH, layer="sindh_roads", driver="GPKG")
gdf_health_proj.to_file(GPKG_PATH, layer="sindh_health_facilities_raw", driver="GPKG")
gdf_settlements_proj.to_file(GPKG_PATH, layer="sindh_settlements", driver="GPKG")
gdf_river_proj.to_file(GPKG_PATH, layer="indus_river", driver="GPKG")

print("\n====================================================================")
print(f" SUCCESS! All standardized layers reprojected to {TARGET_CRS}")
print(f" Datastore saved: '{GPKG_PATH}'")
print(" Layers saved:")
print(f"   - sindh_tehsils ({len(gdf_sindh_tehsils_proj)} polygons)")
print(f"   - sindh_roads ({len(gdf_roads_proj)} line segments)")
print(f"   - sindh_health_facilities_raw ({len(gdf_health_proj)} point features)")
print(f"   - sindh_settlements ({len(gdf_settlements_proj)} point features)")
print(f"   - indus_river ({len(gdf_river_proj)} line segments)")
print("====================================================================\n")
