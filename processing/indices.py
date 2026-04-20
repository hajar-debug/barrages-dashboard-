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
# Dans processing/indices.py

def get_ndti_tile_url(lat, lon, start, end, cloud_pct):
    """Génère l'URL de la couche NDTI (Turbidité) depuis GEE"""
    import ee
    try:
        # On définit la zone (buffer de 5km autour du barrage)
        point = ee.Geometry.Point([lon, lat]).buffer(8000).bounds()
        
        # Collection Sentinel-2
        col = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
               .filterBounds(point)
               .filterDate(start, end)
               .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', cloud_pct))
               .median())

        # Calcul du NDTI : (Red - Green) / (Red + Green)
        # Note : Les bandes S2 sont B4 (Red) et B3 (Green)
        ndti = col.normalizedDifference(['B4', 'B3']).rename('NDTI')

        # Paramètres de visualisation (Brun/Jaune pour la turbidité)
        viz = {'min': -0.1, 'max': 0.3, 'palette': ['#ffffff', '#f1e7d2', '#d2b48c', '#8b4513']}
        
        map_id = ee.data.getMapId({'image': ndti, 'visParams': viz})
        return map_id['tile_fetcher'].url_format
    except Exception as e:
        print(f"Erreur NDTI Tile: {e}")
        return None

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
def get_metrics(lat, lon, start, end, cloud_pct, radius=5000):
    """Calcule tous les indices d'un coup pour gagner du temps."""
    try:
        img = get_base_collection(lat, lon, start, end, cloud_pct)
        # Zone de calcul réduite au centre de la retenue (500m)
        roi_calc = ee.Geometry.Point([lon, lat]).buffer(8000).bounds()
        
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

def water_surface(lat, lon, start, end, cloud_pct, radius=8000):
    """Calcule la surface de la retenue en km²."""
    try:
        # Utilise la variable radius ici si tu veux qu'elle soit dynamique
        roi = ee.Geometry.Point([lon, lat]).buffer(radius).bounds() 
        img = get_base_collection(lat, lon, start, end, cloud_pct)
        ndwi = img.normalizedDifference(['B3', 'B8'])
        water_mask = ndwi.gt(0.1)
        area_m2 = water_mask.multiply(ee.Image.pixelArea()).reduceRegion(
            reducer=ee.Reducer.sum(), geometry=roi, scale=20, maxPixels=1e9
        ).get('nd').getInfo()
        return area_m2 / 1e6
    except: return None

def get_timeseries(lat, lon, start, end, cloud, radius=8000):
    # On utilise maintenant le radius pour créer la zone d'étude
    roi = ee.Geometry.Point([lon, lat]).buffer(radius) 
    
    col = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED") \
        .filterBounds(roi) \
        .filterDate(start, end) \
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', cloud))
    

    def extract_metrics(img):
        date = img.date().format('YYYY-MM-dd')
        
        # NDWI (Eau) - Utilise mean() pour avoir une valeur moyenne sur tout le barrage
        ndwi_img = img.normalizedDifference(['B3', 'B8'])
        ndwi_val = ndwi_img.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=roi,
            scale=30
        ).get('nd')
        
        # NDTI (Turbidité/Sédiments)
        ndti_img = img.normalizedDifference(['B4', 'B3'])
        ndti_val = ndti_img.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=roi,
            scale=30
        ).get('nd')
        
        return ee.Feature(None, {
            'date': date,
            'NDWI': ndwi_val,
            'Turbidité': ndti_val
        })

    try:
        # Transformation GEE -> Liste Python
        info = col.map(extract_metrics).getInfo()
        features = info.get('features', [])
        data = [f['properties'] for f in features if f['properties']['NDWI'] is not None]
        
        df = pd.DataFrame(data)
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
        return df
    except Exception as e:
        print(f"Erreur GEE: {e}")
        return pd.DataFrame()

# À ajouter dans processing/indices.py

def get_rgb_tile_url(lat, lon, start, end, cloud_pct):
    """Génère l'URL de la couche Sentinel-2 en vraies couleurs (RGB)"""
    import ee
    try:
        point = ee.Geometry.Point([lon, lat]).buffer(8000).bounds()
        
        # Sélection des bandes B4 (Red), B3 (Green), B2 (Blue)
        rgb = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
               .filterBounds(point)
               .filterDate(start, end)
               .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', cloud_pct))
               .median()
               .divide(10000)) # Normalisation pour Sentinel-2 SR

        # Paramètres de visualisation pour un rendu naturel
        viz = {
            'bands': ['B4', 'B3', 'B2'],
            'min': 0,
            'max': 0.3,
            'gamma': 1.4
        }
        
        map_id = ee.data.getMapId({'image': rgb, 'visParams': viz})
        return map_id['tile_fetcher'].url_format
    except Exception as e:
        print(f"Erreur RGB Tile: {e}")
        return None
        
def get_water_surface_area(lat, lon, date, cloud, radius=8000):
    roi = ee.Geometry.Point([lon, lat]).buffer(radius)
    img = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED") \
            .filterBounds(roi) \
            .filterDate(ee.Date(date).advance(-1, 'month'), date) \
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', cloud)) \
            .median()

    # Calcul du MNDWI (Green et SWIR)
    mndwi = img.normalizedDifference(['B3', 'B11']).rename('MNDWI')
    
    # Seuil pour isoler l'eau (généralement 0)
    water_mask = mndwi.gt(0)
    
    # Calcul de la surface en km²
    stats = water_mask.multiply(ee.Image.pixelArea()).reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=roi,
        scale=10,
        maxPixels=1e9
    )
    
    area_m2 = stats.get('MNDWI')
    return ee.Number(area_m2).divide(1e6).getInfo() # Retourne des km²
def get_climate_data(lat, lon, date_str):
    # Point de mesure
    roi = ee.Geometry.Point([lon, lat])
    # Collection ERA5-Land (Température à 2m)
    dataset = ee.ImageCollection("ECMWF/ERA5_LAND/HOURLY") \
                .filterBounds(roi) \
                .filterDate(ee.Date(date_str).advance(-7, 'day'), date_str)
    
    temp_img = dataset.select('temperature_2m').mean()
    # Conversion Kelvin en Celsius
    temp_c = temp_img.reduceRegion(ee.Reducer.first(), roi, 1000).get('temperature_2m')
    return float(temp_c.getInfo()) - 273.15
