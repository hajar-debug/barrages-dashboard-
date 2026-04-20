import folium
from folium import plugins
import ee 

def build_map(lat, lon, row, start, end, cloud, show_ndwi, show_ndvi, show_rgb, show_ndti):
    # 1. Zone d'intérêt (ROI) élargie à 5km pour Oued El Makhazine
    roi = ee.Geometry.Point([lon, lat]).buffer(5000)
    
    # 2. Imports locaux des fonctions de calcul d'indices
    from processing.indices import get_ndwi_tile_url, get_ndvi_tile_url, get_rgb_tile_url, get_ndti_tile_url

    # 3. Initialisation de la carte (On utilise folium directement pour éviter le bug geemap)
    m = folium.Map(
        location=[lat, lon],
        zoom_start=12, # Zoom 12 est mieux pour voir les 5km du barrage
        tiles=None,
    )

    # ── 1. FONDS DE CARTE ─────────────────────────────────────────────
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attr='Google',
        name='🛰️ Google Satellite',
        overlay=False,
        control=True
    ).add_to(m)

    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='🌍 Esri Satellite',
        overlay=False,
    ).add_to(m)

    folium.TileLayer(
        tiles='OpenStreetMap',
        name='🗺️ OpenStreetMap',
        overlay=False,
    ).add_to(m)

    # ── 2. COUCHES ANALYTIQUES (Correction des variables cloud) ─────────
    
    # --- COUCHE NDTI (Turbidité) ---
    if show_ndti:
        # On utilise 'cloud' (l'argument de la fonction)
        url = get_ndti_tile_url(lat, lon, start, end, cloud) 
        if url:
            folium.TileLayer(
                tiles=url,
                attr='GEE',
                name='🌫️ Indice NDTI (Turbidité)',
                overlay=True,
                opacity=0.7,
                show=False 
            ).add_to(m)

    # --- COUCHE NDWI (Eau) ---
    if show_ndwi:
        # CORRECTION : cloud_pct remplacé par cloud
        url = get_ndwi_tile_url(lat, lon, start, end, cloud) 
        if url:
            folium.TileLayer(
                tiles=url,
                attr='GEE',
                name='💧 Indice NDWI (Eau)',
                overlay=True,
                opacity=0.7,
                show=True 
            ).add_to(m)

    # --- COUCHE NDVI (Végétation) ---
    if show_ndvi:
        # CORRECTION : cloud_pct remplacé par cloud
        url = get_ndvi_tile_url(lat, lon, start, end, cloud) 
        if url:
            folium.TileLayer(
                tiles=url,
                attr='GEE',
                name='🌿 Indice NDVI (Végétation)',
                overlay=True,
                opacity=0.6,
                show=False 
            ).add_to(m)

    # ── 3. INTERFACE & TOOLS ──────────────────────────────────────────
    folium.LayerControl(position='topright', collapsed=False).add_to(m)
    plugins.Fullscreen().add_to(m)
    plugins.MeasureControl(position='bottomleft').add_to(m)
    
    nom = row.get('barrage', 'Barrage')
    folium.Marker(
        [lat, lon], 
        popup=f"<b>{nom}</b>",
        tooltip=nom,
        icon=folium.Icon(color='blue', icon='tint')
    ).add_to(m)

    return m