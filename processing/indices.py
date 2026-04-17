import ee
import pandas as pd

def get_base_collection(lat, lon, start, end, cloud_pct):
    """Récupère la collection Sentinel-2 sur une Bounding Box de ~25km."""
    # Bounding Box : environ 0.12 degré autour du point
    roi = ee.Geometry.Rectangle([
        lon - 0.12, lat - 0.12, 
        lon + 0.12, lat + 0.12
    ])
    
    return (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
            .filterBounds(roi)
            .filterDate(start, end)
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', cloud_pct))
            .median()
            .clip(roi))

# --- NOUVEAU : INDICE DE TURBIDITÉ (NDTI) ---
def get_ndti_tile_url(lat, lon, start, end, cloud_pct):
    """Génère l'URL pour la carte de turbidité (envasement)."""
    try:
        img = get_base_collection(lat, lon, start, end, cloud_pct)
        # NDTI = (Red - Green) / (Red + Green) -> (B4 - B3)
        ndti = img.normalizedDifference(['B4', 'B3']).rename('NDTI')
        vis_params = {'min': -0.1, 'max': 0.3, 'palette': ['#313695', '#4575b4', '#e0f3f8', '#fee090', '#d73027']}
        return ndti.getMapId(vis_params)['tile_fetcher'].url_format
    except: return None

# --- INDICE D'EAU (NDWI) ---
def get_ndwi_tile_url(lat, lon, start, end, cloud_pct):
    try:
        img = get_base_collection(lat, lon, start, end, cloud_pct)
        ndwi = img.normalizedDifference(['B3', 'B8']).rename('NDWI')
        vis_params = {'min': -0.1, 'max': 0.5, 'palette': ['white', '#00c9ff', '#0066ff', '#001a33']}
        return ndwi.getMapId(vis_params)['tile_fetcher'].url_format
    except: return None

# --- INDICE DE VÉGÉTATION (NDVI) ---
def get_ndvi_tile_url(lat, lon, start, end, cloud_pct):
    try:
        img = get_base_collection(lat, lon, start, end, cloud_pct)
        ndvi = img.normalizedDifference(['B8', 'B4']).rename('NDVI')
        vis_params = {'min': 0, 'max': 0.8, 'palette': ['#ecebf7', '#2db31d', '#1a6b11']}
        return ndvi.getMapId(vis_params)['tile_fetcher'].url_format
    except: return None

# --- CALCUL DES MOYENNES POUR LE TABLEAU DE BORD ---
def get_metrics(lat, lon, start, end, cloud_pct):
    """Calcule tous les indices d'un coup pour gagner du temps."""
    try:
        img = get_base_collection(lat, lon, start, end, cloud_pct)
        # Zone de calcul réduite au centre de la retenue (500m)
        roi_calc = ee.Geometry.Point([lon, lat]).buffer(500).bounds()
        
        ndwi = img.normalizedDifference(['B3', 'B8'])
        ndvi = img.normalizedDifference(['B8', 'B4'])
        ndti = img.normalizedDifference(['B4', 'B3']) # Turbidité
        
        stats = img.addBands([ndwi, ndvi, ndti]).reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=roi_calc,
            scale=10
        )
        
        res = stats.getInfo()
        return {
            "ndwi": res.get('nd'),
            "ndvi": res.get('nd_1'),
            "ndti": res.get('nd_2')
        }
    except: return {"ndwi": None, "ndvi": None, "ndti": None}

def water_surface(lat, lon, start, end, cloud_pct):
    """Calcule la surface de la retenue en km²."""
    try:
        roi = ee.Geometry.Point([lon, lat]).buffer(8000).bounds()
        img = get_base_collection(lat, lon, start, end, cloud_pct)
        ndwi = img.normalizedDifference(['B3', 'B8'])
        water_mask = ndwi.gt(0.1)
        area_m2 = water_mask.multiply(ee.Image.pixelArea()).reduceRegion(
            reducer=ee.Reducer.sum(), geometry=roi, scale=20, maxPixels=1e9
        ).get('nd').getInfo()
        return area_m2 / 1e6
    except: return None

def get_timeseries(lat, lon, start, end, cloud_pct):
    """Génère les données pour le graphique temporel."""
    try:
        roi = ee.Geometry.Point([lon, lat]).buffer(1000).bounds()
        col = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
               .filterBounds(roi).filterDate(start, end)
               .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', cloud_pct)))

        def calc_indices(img):
            ndwi = img.normalizedDifference(['B3', 'B8']).reduceRegion(ee.Reducer.mean(), roi, 20).get('nd')
            ndti = img.normalizedDifference(['B4', 'B3']).reduceRegion(ee.Reducer.mean(), roi, 20).get('nd')
            return ee.Feature(None, {'date': img.date().format('YYYY-MM-DD'), 'NDWI': ndwi, 'Turbidité': ndti})

        features = col.map(calc_indices).getInfo()['features']
        df = pd.DataFrame([f['properties'] for f in features])
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
        return df
    except: return None