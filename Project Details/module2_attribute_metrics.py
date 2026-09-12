import geopandas as gpd

GPKG_PATH = "Sindh_Flood_Analysis.gpkg"
TARGET_CRS = "EPSG:32642"

print("====================================================================")
print("  SDA Lab 1 - Module 2: Attribute Queries & Geometric Metrics       ")
print("====================================================================")

# -------------------------------------------------------------------
# 1. Calculate Tehsil Area in Square Kilometers
# -------------------------------------------------------------------
print("\n[1/3] Calculating Tehsil areas in square kilometers...")

gdf_tehsils = gpd.read_file(GPKG_PATH, layer="sindh_tehsils")

# Calculate area in square kilometers (EPSG:32642 units are in meters)
gdf_tehsils['Tehsil_SqKm'] = (gdf_tehsils.geometry.area / 1_000_000.0).round(2)

print(f"   -> Calculated areas for {len(gdf_tehsils)} Tehsils.")
print(f"   -> Total Sindh Tehsil area analyzed: {gdf_tehsils['Tehsil_SqKm'].sum():,.2f} sq km.")

# Update layer in GeoPackage
gdf_tehsils.to_file(GPKG_PATH, layer="sindh_tehsils", driver="GPKG")

# -------------------------------------------------------------------
# 2. Isolate Arterial High-Capacity Highways
# -------------------------------------------------------------------
print("\n[2/3] Filtering high-capacity arterial highways...")

gdf_roads = gpd.read_file(GPKG_PATH, layer="sindh_roads")

# Attribute Filter: highway IN ('trunk', 'primary') AND surface NOT IN ('unpaved', 'dirt')
filter_arterial = (
    gdf_roads['highway'].isin(['trunk', 'primary']) & 
    (~gdf_roads['surface'].isin(['unpaved', 'dirt']))
)

gdf_arterial_roads = gdf_roads[filter_arterial].copy()

# Calculate segment lengths in km
gdf_arterial_roads['Length_Km'] = (gdf_arterial_roads.geometry.length / 1000.0).round(3)

print(f"   -> Retained {len(gdf_arterial_roads)} arterial highway segments out of {len(gdf_roads)} total road segments.")
print(f"   -> Total arterial road network length: {gdf_arterial_roads['Length_Km'].sum():,.2f} km.")

# Save arterial roads layer
gdf_arterial_roads.to_file(GPKG_PATH, layer="sindh_arterial_roads", driver="GPKG")

# -------------------------------------------------------------------
# 3. Classify Health Facilities
# -------------------------------------------------------------------
print("\n[3/3] Filtering and classifying key health facilities...")

gdf_health = gpd.read_file(GPKG_PATH, layer="sindh_health_facilities_raw")

# Isolate functional hospitals/clinics/DHQ/BHU
filter_health = (
    gdf_health['amenity'].isin(['hospital', 'clinic']) |
    gdf_health['name'].str.contains('DHQ|BHU|Basic Health|District Headquarter', case=False, na=False)
)

gdf_health_facilities = gdf_health[filter_health].copy()

print(f"   -> Extracted {len(gdf_health_facilities)} functional healthcare facilities.")

# Save classified health facilities layer
gdf_health_facilities.to_file(GPKG_PATH, layer="sindh_health_facilities", driver="GPKG")

print("\n====================================================================")
print(" SUCCESS! Module 2 Complete. GeoPackage updated with:")
print("   - sindh_tehsils (with 'Tehsil_SqKm' field)")
print(f"   - sindh_arterial_roads ({len(gdf_arterial_roads)} segments, 'Length_Km' field)")
print(f"   - sindh_health_facilities ({len(gdf_health_facilities)} point features)")
print("====================================================================\n")
