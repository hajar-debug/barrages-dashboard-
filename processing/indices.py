import ee
import pandas as pd
import streamlit as st
# --- ÉTAPE 1 : La fonction qui choisit Watershed ou Buffer ---
def get_study_area(lat, lon, radius=15000):
    try:
        point = ee.Geometry.Point([lon, lat])
        # On cherche le bassin versant HydroSHEDS (Niveau 12)
        basins = ee.FeatureCollection("WWF/HydroSHEDS/v1/Basins/hybas_12")
        watershed = basins.filterBounds(point).first()
        
        # Si le bassin est trouvé, on l'utilise, sinon on fait un cercle (buffer)
        if watershed is not None:
            return watershed.geometry()
        else:
            return point.buffer(radius)
    except:
        # En cas de bug GEE, on retourne le cercle par sécurité
        return ee.Geometry.Point([lon, lat]).buffer(radius)

# --- ÉTAPE 2 : Ta fonction 2020 mise à jour ---
@st.cache_data
def get_annual_reference_2020(lat, lon):
    # On appelle la fonction intelligente définie juste au-dessus
    roi = get_study_area(lat, lon)
    
    try:
        annual_2020 = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                       .filterBounds(roi)
                       .filterDate('2020-01-01', '2020-12-31')
                       .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
                       .median())
        
        ndwi = annual_2020.normalizedDifference(['B3', 'B8']).rename('NDWI')
        water_mask = ndwi.gt(0)
        
        area_image = water_mask.multiply(ee.Image.pixelArea())
        stats = area_image.reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=roi,
            scale=30, # On met 30m pour que ce soit rapide sur 6200 km2
            maxPixels=1e9
        )
        
        surface = ee.Number(stats.get('NDWI')).divide(1e6).getInfo()
        return surface if surface is not None else 12.5
    except:
        return 12.5

def get_base_collection(lat, lon, start, end, cloud_pct, radius=12000):
    """Récupère la collection Sentinel-2 optimisée pour le calcul de surface."""
    roi = get_study_area(lat, lon, radius)
    
    col = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
            .filterBounds(roi)
            .filterDate(start, end)
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', cloud_pct))
            .median()
            .clip(roi))
    return col

# --- NOUVEAU : INDICE DE TURBIDITÉ (NDTI) ---
# Dans processing/indices.py

def get_ndti_tile_url(lat, lon, start, end, cloud_pct):
    """Génère l'URL de la couche NDTI (Turbidité) depuis GEE"""
    import ee
    try:
        # On définit la zone (buffer de 5km autour du barrage)
        point = ee.Geometry.Point([lon, lat]).buffer(12000).bounds()
        
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
def get_metrics(lat, lon, start_date, end_date, cloud_pct, radius=5000):
    try:
        roi = get_study_area(lat, lon, radius)
        
        # On charge Sentinel-2
        collection = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED") \
            .filterBounds(roi) \
            .filterDate(start_date, end_date) \
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', cloud_pct))
        
        # On prend la mosaïque la plus propre (médiane)
        image = collection.median().clip(roi)
        
        # On calcule les indices (Noms de bandes exacts)
        # MNDWI = (Green - SWIR) / (Green + SWIR)
        ndwi = image.normalizedDifference(['B3', 'B11']).rename('ndwi')
        # NDVI = (NIR - Red) / (NIR + Red)
        ndvi = image.normalizedDifference(['B8', 'B4']).rename('ndvi')
        # NDTI = (Red - Green) / (Red + Green)
        ndti = image.normalizedDifference(['B4', 'B3']).rename('ndti')
        
        # RÉDUCTION : On transforme l'image en chiffres (Moyenne sur la zone)
        stats = ee.Image.cat([ndwi, ndvi, ndti]).reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=roi,
            scale=30,
            maxPixels=1e9
        ).getInfo()
        
        return stats # Renvoie {'ndwi': 0.XX, 'ndvi': 0.XX, 'ndti': 0.XX}
    except Exception as e:
        return {"ndwi": None, "ndvi": None, "ndti": None}

def water_surface(lat, lon, start, end, cloud_pct, radius=12000):
    """Calcule la surface avec le seuil MNDWI corrigé pour le Maroc."""
    try:
        roi = get_study_area(lat, lon, radius)
        
        # On récupère l'image médiane
        img = get_base_collection(lat, lon, start, end, cloud_pct, radius)
        
        # MNDWI (B3, B11) est plus robuste que le NDWI classique pour les sédiments
        mndwi = img.normalizedDifference(['B3', 'B11']).rename('mndwi')
         
        # SEUIL CRITIQUE : On passe à 0.0 pour ne pas perdre de surface en hiver
        water_mask = mndwi.gt(0.0) 
        
        area_m2 = water_mask.multiply(ee.Image.pixelArea()).reduceRegion(
            reducer=ee.Reducer.sum(), 
            geometry=roi, 
            scale=30, 
            maxPixels=1e9
        ).get('mndwi').getInfo()
        
        return area_m2 / 1e6 if area_m2 else 0
    except Exception as e:
        return 0

def get_timeseries(lat, lon, start, end, cloud, radius=15000):
    # MODIFICATION ICI
    roi = get_study_area(lat, lon, radius)
    
    col = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED") \
        .filterBounds(roi) \
        .filterDate(start, end) \
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', cloud))

    def extract_metrics(img):
        date = img.date().format('YYYY-MM-dd')
        
        # Réduction sur la ROI du bassin
        ndwi_val = img.normalizedDifference(['B3', 'B8']).reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=roi,
            scale=50 # MODIFICATION : 50m pour les séries temporelles (plus rapide)
        ).get('nd')
        
        ndti_val = img.normalizedDifference(['B4', 'B3']).reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=roi,
            scale=50
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
        point = ee.Geometry.Point([lon, lat]).buffer(12000).bounds()
        
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
        
def get_water_surface_area(lat, lon, date, cloud, radius=12000):
    roi = get_study_area(lat, lon, radius)
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
        scale=30,
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

@st.cache_data(ttl=3600) # Garde les résultats en mémoire 1 heure
def get_metrics_cached(lat, lon, start, end, cloud):
    return get_metrics(lat, lon, start, end, cloud)
    