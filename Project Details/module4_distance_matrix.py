import sys
import geopandas as gpd
import pandas as pd
import numpy as np
from scipy.spatial import KDTree

# Set stdout encoding to UTF-8 for Windows console support
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

GPKG_PATH = "Sindh_Flood_Analysis.gpkg"
TARGET_CRS = "EPSG:32642"

print("====================================================================")
print("  SDA Lab 1 - Module 4: Accessibility & Distance Matrix Analysis     ")
print("====================================================================")

# -------------------------------------------------------------------
# 1. Identify Operational Health Facilities (Active Health Centers)
# -------------------------------------------------------------------
print("\n[1/3] Filtering Operational (Unflooded) Health Facilities...")

gdf_health = gpd.read_file(GPKG_PATH, layer="sindh_health_facilities")
gdf_buffer_3km = gpd.read_file(GPKG_PATH, layer="indus_buffer_3km")

# Identify health facilities inside the 3 km flood zone
health_flooded_join = gpd.sjoin(gdf_health, gdf_buffer_3km, how='inner', predicate='within')
flooded_health_ids = health_flooded_join.index.unique()

# Unflooded health facilities = facilities NOT in the 3 km flood zone
gdf_active_health = gdf_health[~gdf_health.index.isin(flooded_health_ids)].copy()

print(f"   -> Total Health Facilities: {len(gdf_health)}")
print(f"   -> Inundated Health Facilities (within 3km flood buffer): {len(flooded_health_ids)}")
print(f"   -> Operational (Active) Health Centers: {len(gdf_active_health)}")

# Save active health centers layer
gdf_active_health.to_file(GPKG_PATH, layer="active_health_centers", driver="GPKG")
print("   -> Saved layer 'active_health_centers' to GeoPackage.")

# -------------------------------------------------------------------
# 2. Euclidean Distance Matrix Computation (Settlements -> Health Centers)
# -------------------------------------------------------------------
print("\n[2/3] Computing Distance Matrix for Settlement Points...")

gdf_settlements = gpd.read_file(GPKG_PATH, layer="sindh_settlements")
print(f"   -> Loaded {len(gdf_settlements)} settlement origin points.")

# Prepare Cartesian XY coordinates (in EPSG:32642 meters)
settlement_coords = np.column_stack([gdf_settlements.geometry.x, gdf_settlements.geometry.y])
all_health_coords = np.column_stack([gdf_health.geometry.x, gdf_health.geometry.y])
active_health_coords = np.column_stack([gdf_active_health.geometry.x, gdf_active_health.geometry.y])

# KD-Tree for 1-Nearest Neighbor Distance Calculation
tree_all = KDTree(all_health_coords)
tree_active = KDTree(active_health_coords)

dist_baseline_m, idx_baseline = tree_all.query(settlement_coords)
dist_inundated_m, idx_active = tree_active.query(settlement_coords)

gdf_settlements['Baseline_Dist_Km'] = (dist_baseline_m / 1000.0).round(3)
gdf_settlements['Inundated_Dist_Km'] = (dist_inundated_m / 1000.0).round(3)
gdf_settlements['Distance_Increase_Km'] = (gdf_settlements['Inundated_Dist_Km'] - gdf_settlements['Baseline_Dist_Km']).round(3)

# Attach nearest active health center name
gdf_settlements['Nearest_Active_Center'] = gdf_active_health.iloc[idx_active]['name'].values

# Save updated settlements layer
gdf_settlements.to_file(GPKG_PATH, layer="sindh_settlements", driver="GPKG")
print("   -> Updated 'sindh_settlements' layer with accessibility distance metrics.")

# -------------------------------------------------------------------
# 3. Identify Top 3 Most Isolated Settlement Points
# -------------------------------------------------------------------
print("\n[3/3] Identifying Top 3 Settlements Facing Greatest Distance Increases...")

top3_isolated = gdf_settlements.sort_values(by='Distance_Increase_Km', ascending=False).head(3)

print("\n====================================================================")
print(" TOP 3 MOST ISOLATED SETTLEMENTS:")
print("====================================================================")
for idx, row in top3_isolated.iterrows():
    name_str = str(row['name']).encode('ascii', errors='replace').decode('ascii')
    place_str = str(row['place']).encode('ascii', errors='replace').decode('ascii')
    center_str = str(row['Nearest_Active_Center']).encode('ascii', errors='replace').decode('ascii')
    print(f" Name: {name_str} (Original: {repr(row['name'])}) | Place: {place_str}")
    print(f"   - Baseline Distance to Health Center: {row['Baseline_Dist_Km']:.2f} km")
    print(f"   - Inundated Distance to Operational Health Center: {row['Inundated_Dist_Km']:.2f} km")
    print(f"   - Net Distance Increase (Isolation Impact): +{row['Distance_Increase_Km']:.2f} km")
    print(f"   - Nearest Operational Center: {center_str}")
    print("--------------------------------------------------------------------")

# -------------------------------------------------------------------
# 4. Generate GIS402_Lab1_Metrics_Summary.csv Table
# -------------------------------------------------------------------
print("\n[4/4] Generating Summary Table CSV: 'GIS402_Lab1_Metrics_Summary.csv'...")

gdf_tehsils = gpd.read_file(GPKG_PATH, layer="sindh_tehsils")
gdf_inundated_roads = gpd.read_file(GPKG_PATH, layer="inundated_arterial_roads")
gdf_inundated_with_tehsil = gpd.sjoin(gdf_inundated_roads, gdf_tehsils[['ADM2_EN', 'ADM3_EN', 'geometry']], how='left', predicate='intersects')

road_summary = gdf_inundated_with_tehsil.groupby(['ADM2_EN', 'ADM3_EN'])['Segment_Length_Km'].sum().reset_index()
road_summary = road_summary.rename(columns={'Segment_Length_Km': 'Inundated_Road_Km'})

tehsil_summary = gdf_tehsils[['ADM1_EN', 'ADM2_EN', 'ADM3_EN', 'Tehsil_SqKm', 'Health_Count']].copy()
summary_df = tehsil_summary.merge(road_summary, on=['ADM2_EN', 'ADM3_EN'], how='left')
summary_df['Inundated_Road_Km'] = summary_df['Inundated_Road_Km'].fillna(0.0).round(2)

csv_path = "GIS402_Lab1_Metrics_Summary.csv"
summary_df.to_csv(csv_path, index=False, encoding='utf-8')
print(f"   -> Summary table successfully created and saved to '{csv_path}'.")

print("\n====================================================================")
print(" SUCCESS! Modules 3 & 4 Complete. All spatial metrics compiled.")
print("====================================================================\n")
