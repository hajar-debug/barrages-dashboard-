import ee
import pandas as pd

# ❌ SUPPRESSION DU BLOC ee.Initialize() / ee.Authenticate()
# La connexion se fait maintenant via gee_init.py appelé dans app.py

COLLECTION = "COPERNICUS/S2_SR_HARMONIZED"

def _base_collection(lat, lon, start, end, cloud_pct=20, buffer=5000):
    point = ee.Geometry.Point([lon, lat]).buffer(buffer)
    return (
        ee.ImageCollection(COLLECTION)
        .filterBounds(point)
        .filterDate(start, end)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", cloud_pct))
    )

def get_ndwi_mean(lat, lon, start, end, cloud_pct=20):
    point = ee.Geometry.Point([lon, lat])
    col = _base_collection(lat, lon, start, end, cloud_pct, buffer=100)
    def calc(img):
        return img.normalizedDifference(["B3", "B8"]).rename("NDWI") \
                  .copyProperties(img, img.propertyNames())
    try:
        value = (col.map(calc).mean()
                .reduceRegion(reducer=ee.Reducer.mean(), geometry=point, scale=30, maxPixels=1e13)
                .get("NDWI"))
        return ee.Number(value).getInfo()
    except:
        return None

def get_ndvi_mean(lat, lon, start, end, cloud_pct=20):
    point = ee.Geometry.Point([lon, lat])
    col = _base_collection(lat, lon, start, end, cloud_pct, buffer=100)
    def calc(img):
        return img.normalizedDifference(["B8", "B4"]).rename("NDVI") \
                  .copyProperties(img, img.propertyNames())
    try:
        value = (col.map(calc).mean()
                .reduceRegion(reducer=ee.Reducer.mean(), geometry=point, scale=30, maxPixels=1e13)
                .get("NDVI"))
        return ee.Number(value).getInfo()
    except:
        return None

def water_surface(lat, lon, start, end, cloud_pct=20):
    point = ee.Geometry.Point([lon, lat]).buffer(5000)
    col = _base_collection(lat, lon, start, end, cloud_pct, buffer=5000)
    def calc(img):
        return img.normalizedDifference(["B3", "B8"]).rename("NDWI") \
                  .copyProperties(img, img.propertyNames())
    try:
        ndwi_img = col.map(calc).median()
        area = (ndwi_img.gt(0.2)
                .multiply(ee.Image.pixelArea())
                .reduceRegion(reducer=ee.Reducer.sum(), geometry=point, scale=30, maxPixels=1e13)
                .get("NDWI"))
        return ee.Number(area).divide(1e6).getInfo()
    except:
        return None

def get_timeseries(lat, lon, start, end, cloud_pct=20):
    point = ee.Geometry.Point([lon, lat])
    col = _base_collection(lat, lon, start, end, cloud_pct, buffer=100)
    def calc(img):
        ndwi = img.normalizedDifference(["B3", "B8"]).rename("NDWI")
        ndvi = img.normalizedDifference(["B8", "B4"]).rename("NDVI")
        stats = ndwi.addBands(ndvi).reduceRegion(reducer=ee.Reducer.mean(), geometry=point, scale=30)
        return img.set("NDWI_mean", stats.get("NDWI")).set("NDVI_mean", stats.get("NDVI"))
    try:
        data = col.map(calc).reduceColumns(ee.Reducer.toList(3), ["system:time_start", "NDWI_mean", "NDVI_mean"]).get("list").getInfo()
        df = pd.DataFrame(data, columns=["date", "NDWI", "NDVI"])
        df["date"] = pd.to_datetime(df["date"], unit="ms")
        return df.dropna().sort_values("date")
    except:
        return None

def get_ndwi_tile_url(lat, lon, start, end, cloud_pct=20):
    try:
        col = _base_collection(lat, lon, start, end, cloud_pct, buffer=20000)
        ndwi_img = col.map(lambda img: img.normalizedDifference(["B3", "B8"])).median()
        vis = {"min": -0.3, "max": 0.6, "palette": ["#8B4513", "#FFFFE0", "#00BFFF", "#00008B"]}
        return ndwi_img.getMapId(vis)["tile_fetcher"].url_format
    except: return None

def get_ndvi_tile_url(lat, lon, start, end, cloud_pct=20):
    try:
        col = _base_collection(lat, lon, start, end, cloud_pct, buffer=20000)
        ndvi_img = col.map(lambda img: img.normalizedDifference(["B8", "B4"])).median()
        vis = {"min": -0.2, "max": 0.8, "palette": ["#d73027", "#ffffbf", "#1a9850"]}
        return ndvi_img.getMapId(vis)["tile_fetcher"].url_format
    except: return None

def get_rgb_tile_url(lat, lon, start, end, cloud_pct=20):
    try:
        col = _base_collection(lat, lon, start, end, cloud_pct, buffer=20000)
        rgb_img = col.median().select(["B4", "B3", "B2"])
        vis = {"min": 0, "max": 3000, "bands": ["B4", "B3", "B2"]}
        return rgb_img.getMapId(vis)["tile_fetcher"].url_format
    except: return None
    