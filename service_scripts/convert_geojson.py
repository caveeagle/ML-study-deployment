import geopandas as gpd

gdf = gpd.read_file("../shapefiles/belgium_map_simplified.shp")

gdf.to_file("../data/belgium_map.geojson", driver="GeoJSON")

print('Job finished')
