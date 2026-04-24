import folium
from folium import plugins
import ee 
import geopandas as gpd # <--- Ajout crucial

def build_map(lat, lon, row, start, end, cloud, show_ndwi, show_ndvi, show_rgb, show_ndti, radius=5000):
    # 1. Zone d'intérêt (ROI) basée sur le radius dynamique
    roi = ee.Geometry.Point([lon, lat]).buffer(radius)
    
    # 2. Imports locaux
    from processing.indices import get_ndwi_tile_url, get_ndvi_tile_url, get_rgb_tile_url, get_ndti_tile_url

    # 3. Initialisation de la carte
    m = folium.Map(
        location=[lat, lon],
        zoom_start=13 if radius < 6000 else 11, # Zoom adaptatif selon la taille du barrage
        tiles=None,
    )

    # ── 1. FONDS DE CARTE ─────────────────────────────────────────────
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attr='Google', name='🛰️ Google Satellite', overlay=False
    ).add_to(m)

    folium.TileLayer(
        tiles='OpenStreetMap', name='🗺️ OpenStreetMap', overlay=False
    ).add_to(m)

    # ── 2. COUCHES SIG (VERSION SÉCURISÉE) ─────────────────────────────
    try:
        # Affichage simple des Communes
        folium.GeoJson(
            "Data/communes.geojson",
            name="🏡 Limites Communales",
            style_function=lambda x: {'fillColor': 'none', 'color': '#7f8c8d', 'weight': 1, 'dashArray': '4, 4'},
            control=True
        ).add_to(m)

        # Affichage simple des Provinces
        folium.GeoJson(
            "Data/provinces.geojson",
            name="🏢 Limites Provinciales",
            style_function=lambda x: {'fillColor': 'none', 'color': '#c1272d', 'weight': 2},
            control=True
        ).add_to(m)
    except Exception as e:
        print(f"Note: Couches SIG non chargées : {e}")

    # ── 3. COUCHES ANALYTIQUES GEE ─────────────────────────────────────
    
    # NDTI (Turbidité)
    if show_ndti:
        url = get_ndti_tile_url(lat, lon, start, end, cloud) 
        if url:
            folium.TileLayer(tiles=url, attr='GEE', name='🌫️ Turbidité', overlay=True, opacity=0.7, show=False).add_to(m)

    # NDWI (Eau) - CORRIGÉ AVEC MNDWI DANS INDICES.PY
    if show_ndwi:
        url = get_ndwi_tile_url(lat, lon, start, end, cloud) 
        if url:
            folium.TileLayer(tiles=url, attr='GEE', name='💧 Surface en Eau', overlay=True, opacity=0.8, show=True).add_to(m)

    # NDVI (Végétation)
    if show_ndvi:
        url = get_ndvi_tile_url(lat, lon, start, end, cloud) 
        if url:
            folium.TileLayer(tiles=url, attr='GEE', name='🌿 Végétation', overlay=True, opacity=0.6, show=False).add_to(m)

    # ── 4. INTERFACE & TOOLS ──────────────────────────────────────────
    folium.LayerControl(position='topright', collapsed=False).add_to(m)
    plugins.Fullscreen().add_to(m)
    plugins.MeasureControl(position='bottomleft').add_to(m)
    
    # Marqueur stylisé pour le barrage
    nom = row.get('barrage', 'Barrage')
    folium.Marker(
        [lat, lon], 
        popup=f"<b>{nom}</b><br>Capacité: {row.get('capacite', '-')} Mm³",
        icon=folium.Icon(color='darkblue', icon='info-sign')
    ).add_to(m)

    return m
