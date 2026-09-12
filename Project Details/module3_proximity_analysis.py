import geopandas as gpd
import pandas as pd
from shapely.geometry import MultiPolygon, Polygon

GPKG_PATH = "Sindh_Flood_Analysis.gpkg"
TARGET_CRS = "EPSG:32642"

print("====================================================================")
print("  SDA Lab 1 - Module 3: Proximity Analysis & Spatial Overlays       ")
print("====================================================================")

# -------------------------------------------------------------------
# 1. Hydrological Multi-Ring Buffering around Indus River
# -------------------------------------------------------------------
print("\n[1/3] Generating Multi-Ring Hydrological Flood Hazard Buffers...")

gdf_river = gpd.read_file(GPKG_PATH, layer="indus_river")
print(f"   -> Loaded Indus River mainstem layer ({len(gdf_river)} line segments).")

buffer_specs = [
    (1000, "High Hazard Zone (1km)", "indus_buffer_1km"),
    (3000, "Moderate Hazard Zone (3km)", "indus_buffer_3km"),
    (5000, "Extended Risk Zone (5km)", "indus_buffer_5km")
]

buffer_gdfs = []

for dist_m, zone_name, layer_name in buffer_specs:
    # Optimized: Buffer each segment first then perform fast binary cascading union
    buf_geom = gdf_river.geometry.buffer(dist_m).union_all()
    buf_gdf = gpd.GeoDataFrame(
        [{'hazard_zone': zone_name, 'buffer_dist_m': dist_m, 'geometry': buf_geom}],
        crs=TARGET_CRS
    )
    # Save individual layer
    buf_gdf.to_file(GPKG_PATH, layer=layer_name, driver="GPKG")
    buffer_gdfs.append(buf_gdf)
    print(f"   -> Created & saved layer '{layer_name}' ({dist_m}m buffer).")

# Create combined buffer layer for multi-ring representation
gdf_all_buffers = pd.concat(buffer_gdfs, ignore_index=True)
gdf_all_buffers = gpd.GeoDataFrame(gdf_all_buffers, crs=TARGET_CRS)
gdf_all_buffers.to_file(GPKG_PATH, layer="indus_river_buffers", driver="GPKG")
print("   -> Created & saved combined layer 'indus_river_buffers'.")

# -------------------------------------------------------------------
# 2. Inundated Road Network Intersect (Arterial Highways in 3 km Buffer)
# -------------------------------------------------------------------
print("\n[2/3] Performing Spatial Intersection for Inundated Arterial Highways...")

gdf_arterial_roads = gpd.read_file(GPKG_PATH, layer="sindh_arterial_roads")
gdf_buffer_3km = gpd.read_file(GPKG_PATH, layer="indus_buffer_3km")

# Execute spatial overlay intersection
gdf_inundated_roads = gpd.overlay(gdf_arterial_roads, gdf_buffer_3km, how='intersection')

# Calculate impacted segment lengths in kilometers
gdf_inundated_roads['Segment_Length_Km'] = (gdf_inundated_roads.geometry.length / 1000.0).round(3)

total_inundated_km = gdf_inundated_roads['Segment_Length_Km'].sum()
print(f"   -> Total arterial highway length in 3 km flood buffer: {total_inundated_km:,.2f} km")
print(f"   -> Total impacted road segments: {len(gdf_inundated_roads)}")

# Save inundated roads layer
gdf_inundated_roads.to_file(GPKG_PATH, layer="inundated_arterial_roads", driver="GPKG")
print("   -> Saved layer 'inundated_arterial_roads' to GeoPackage.")

# Spatial join with Tehsils to identify most impacted Tehsil
gdf_tehsils = gpd.read_file(GPKG_PATH, layer="sindh_tehsils")
gdf_inundated_with_tehsil = gpd.sjoin(gdf_inundated_roads, gdf_tehsils[['ADM2_EN', 'ADM3_EN', 'geometry']], how='left', predicate='intersects')

road_by_tehsil = gdf_inundated_with_tehsil.groupby(['ADM2_EN', 'ADM3_EN'])['Segment_Length_Km'].sum().reset_index()
road_by_tehsil = road_by_tehsil.sort_values(by='Segment_Length_Km', ascending=False)

top_tehsil = road_by_tehsil.iloc[0]
print(f"   -> Most Impacted Tehsil: {top_tehsil['ADM3_EN']} ({top_tehsil['ADM2_EN']} District) with {top_tehsil['Segment_Length_Km']:.2f} km inundated roads.")

# -------------------------------------------------------------------
# 3. Point-in-Polygon Healthcare Facility Aggregation
# -------------------------------------------------------------------
print("\n[3/3] Aggregating Healthcare Facilities by Tehsil (Point-in-Polygon)...")

gdf_health = gpd.read_file(GPKG_PATH, layer="sindh_health_facilities")

# Spatial join to associate each health facility with a Tehsil
health_joined = gpd.sjoin(gdf_health, gdf_tehsils[['ADM3_EN', 'geometry']], how='inner', predicate='within')
health_counts = health_joined.groupby('ADM3_EN').size().reset_index(name='Health_Count')

# Merge counts back to Tehsil polygons
gdf_tehsils_updated = gdf_tehsils.merge(health_counts, on='ADM3_EN', how='left')
gdf_tehsils_updated['Health_Count'] = gdf_tehsils_updated['Health_Count'].fillna(0).astype(int)

# Update layer in GeoPackage
gdf_tehsils_updated.to_file(GPKG_PATH, layer="sindh_tehsils", driver="GPKG")
print(f"   -> Updated 'sindh_tehsils' layer with 'Health_Count' field.")
print(f"   -> Total healthcare facilities mapped to Tehsils: {gdf_tehsils_updated['Health_Count'].sum()}")

# Check Healthcare Inaccessibility (1 km High Hazard Zone)
gdf_buffer_1km = gpd.read_file(GPKG_PATH, layer="indus_buffer_1km")
gdf_health_1km = gpd.sjoin(gdf_health, gdf_buffer_1km, how='inner', predicate='within')
health_1km_count = len(gdf_health_1km)
pct_1km = (health_1km_count / len(gdf_health)) * 100.0

print("\n--------------------------------------------------------------------")
print(" MODULE 3 PRELIMINARY METRICS SUMMARY:")
print(f" 1. Total Inundated Arterial Roads (3 km Buffer): {total_inundated_km:,.2f} km")
print(f" 2. Top Impacted Tehsil: {top_tehsil['ADM3_EN']} ({top_tehsil['ADM2_EN']} District) - {top_tehsil['Segment_Length_Km']:.2f} km")
print(f" 3. Health Facilities in High Hazard Zone (1 km Buffer): {health_1km_count} out of {len(gdf_health)} ({pct_1km:.2f}%)")
print("====================================================================\n")
