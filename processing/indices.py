import ee
import pandas as pd
import ee

try:
    ee.Initialize(project="barrages-project")
except Exception:
    ee.Authenticate()
    ee.Initialize(project="barrages-project")

COLLECTION = "COPERNICUS/S2_SR_HARMONIZED"


def _base_collection(lat, lon, start, end, cloud_pct=20, buffer=5000):
    point = ee.Geometry.Point([lon, lat]).buffer(buffer)
    return (
        ee.ImageCollection(COLLECTION)
        .filterBounds(point)
        .filterDate(start, end)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", cloud_pct))
    )


# ── NDWI ──────────────────────────────────────────────────────────────────────
def get_ndwi_mean(lat, lon, start, end, cloud_pct=20):
    point = ee.Geometry.Point([lon, lat])
    col = _base_collection(lat, lon, start, end, cloud_pct, buffer=100)

    def calc(img):
        return img.normalizedDifference(["B3", "B8"]).rename("NDWI") \
                  .copyProperties(img, img.propertyNames())

    value = (
        col.map(calc).mean()
        .reduceRegion(reducer=ee.Reducer.mean(), geometry=point, scale=30, maxPixels=1e13)
        .get("NDWI")
    )
    try:
        return ee.Number(value).getInfo()
    except Exception:
        return None


# ── NDVI ──────────────────────────────────────────────────────────────────────
def get_ndvi_mean(lat, lon, start, end, cloud_pct=20):
    point = ee.Geometry.Point([lon, lat])
    col = _base_collection(lat, lon, start, end, cloud_pct, buffer=100)

    def calc(img):
        return img.normalizedDifference(["B8", "B4"]).rename("NDVI") \
                  .copyProperties(img, img.propertyNames())

    value = (
        col.map(calc).mean()
        .reduceRegion(reducer=ee.Reducer.mean(), geometry=point, scale=30, maxPixels=1e13)
        .get("NDVI")
    )
    try:
        return ee.Number(value).getInfo()
    except Exception:
        return None


# ── Surface eau ───────────────────────────────────────────────────────────────
def water_surface(lat, lon, start, end, cloud_pct=20):
    point = ee.Geometry.Point([lon, lat]).buffer(5000)
    col = _base_collection(lat, lon, start, end, cloud_pct, buffer=5000)

    def calc(img):
        return img.normalizedDifference(["B3", "B8"]).rename("NDWI") \
                  .copyProperties(img, img.propertyNames())

    ndwi_img = col.map(calc).median()
    area = (
        ndwi_img.gt(0.2)
        .multiply(ee.Image.pixelArea())
        .reduceRegion(reducer=ee.Reducer.sum(), geometry=point, scale=30, maxPixels=1e13)
        .get("NDWI")
    )
    try:
        return ee.Number(area).divide(1e6).getInfo()
    except Exception:
        return None


# ── Séries temporelles mensuelles ─────────────────────────────────────────────
def get_timeseries(lat, lon, start, end, cloud_pct=20):
    """Retourne un DataFrame avec colonnes date, NDWI, NDVI."""
    point = ee.Geometry.Point([lon, lat])
    col = _base_collection(lat, lon, start, end, cloud_pct, buffer=100)

    def calc(img):
        ndwi = img.normalizedDifference(["B3", "B8"]).rename("NDWI")
        ndvi = img.normalizedDifference(["B8", "B4"]).rename("NDVI")
        combined = ndwi.addBands(ndvi)
        stats = combined.reduceRegion(
            reducer=ee.Reducer.mean(), geometry=point, scale=30, maxPixels=1e13
        )
        return img.set("NDWI_mean", stats.get("NDWI")) \
                  .set("NDVI_mean", stats.get("NDVI"))

    try:
        result = col.map(calc).aggregate_array("system:time_start") \
                   .getInfo()
        ndwi_vals = col.map(calc).aggregate_array("NDWI_mean").getInfo()
        ndvi_vals = col.map(calc).aggregate_array("NDVI_mean").getInfo()
        dates = [pd.to_datetime(t, unit="ms") for t in result]

        df = pd.DataFrame({"date": dates, "NDWI": ndwi_vals, "NDVI": ndvi_vals})
        df = df.dropna().sort_values("date")
        return df
    except Exception:
        return None


# ── Couche NDWI pour carte (URL tiles) ───────────────────────────────────────
def get_ndwi_tile_url(lat, lon, start, end, cloud_pct=20):
    col = _base_collection(lat, lon, start, end, cloud_pct, buffer=20000)

    def calc(img):
        return img.normalizedDifference(["B3", "B8"]).rename("NDWI")

    ndwi_img = col.map(calc).median()
    vis = {"min": -0.3, "max": 0.6, "palette": ["#8B4513", "#FFFFE0", "#00BFFF", "#00008B"]}
    try:
        url = ndwi_img.getMapId(vis)
        return url["tile_fetcher"].url_format
    except Exception:
        return None


# ── Couche NDVI pour carte ────────────────────────────────────────────────────
def get_ndvi_tile_url(lat, lon, start, end, cloud_pct=20):
    col = _base_collection(lat, lon, start, end, cloud_pct, buffer=20000)

    def calc(img):
        return img.normalizedDifference(["B8", "B4"]).rename("NDVI")

    ndvi_img = col.map(calc).median()
    vis = {"min": -0.2, "max": 0.8, "palette": ["#d73027", "#ffffbf", "#1a9850"]}
    try:
        url = ndvi_img.getMapId(vis)
        return url["tile_fetcher"].url_format
    except Exception:
        return None


# ── Couche RGB ────────────────────────────────────────────────────────────────
def get_rgb_tile_url(lat, lon, start, end, cloud_pct=20):
    col = _base_collection(lat, lon, start, end, cloud_pct, buffer=20000)
    rgb_img = col.median().select(["B4", "B3", "B2"])
    vis = {"min": 0, "max": 3000, "bands": ["B4", "B3", "B2"]}
    try:
        url = rgb_img.getMapId(vis)
        return url["tile_fetcher"].url_format
    except Exception:
        return None

