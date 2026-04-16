import ee

ee.Initialize(project='barrages-project')  # remplace si besoin

# 📍 point exemple (Maroc)
point = ee.Geometry.Point([34.5980484, -5.19720249983])

# 🛰️ image Sentinel-2
image = (ee.ImageCollection("COPERNICUS/S2_HARMONIZED")
    .filterBounds(point)
    .filterDate("2023-01-01", "2023-12-31")
    .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20))
    .median()
)

# 💧 NDWI = eau
ndwi = image.normalizedDifference(["B3", "B8"])

# 📊 extraction valeur
value = ndwi.reduceRegion(
    reducer=ee.Reducer.mean(),
    geometry=point,
    scale=30
).getInfo()

print("NDWI result :", value)
