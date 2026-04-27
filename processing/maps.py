import folium
from folium import plugins
import ee 

def build_map(lat, lon, row, start, end, cloud, show_ndwi, show_ndvi, show_rgb, show_ndti, radius=8000):
    # ── 1. CALCUL DU RECTANGLE (AOI) ──
    # Conversion approximative : 0.01 degré ~ 1.1km
    # On crée une emprise de sécurité autour du point central
    delta = 0.07  # Environ 7-8 km autour du point
    bbox_folium = [[lat - delta, lon - delta], [lat + delta, lon + delta]]
    
    # Imports des fonctions de tuiles GEE
    from processing.indices import get_ndwi_tile_url, get_ndvi_tile_url, get_ndti_tile_url

    # 2. Initialisation de la carte
    m = folium.Map(
        location=[lat, lon],
        zoom_start=11, 
        tiles=None,
    )

    # 3. Fonds de carte (Satellite et Plan)
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attr='Google Satellite', name='🛰️ Satellite', overlay=False
    ).add_to(m)

    folium.TileLayer(tiles='OpenStreetMap', name='🗺️ Plan', overlay=False).add_to(m)

    # 4. Couches Télédétection (GEE)
    if show_ndti:
        url = get_ndti_tile_url(lat, lon, start, end, cloud) 
        if url:
            folium.TileLayer(tiles=url, attr='GEE', name='🌫️ Turbidité', overlay=True, opacity=0.7, show=False).add_to(m)

    if show_ndwi:
        url = get_ndwi_tile_url(lat, lon, start, end, cloud) 
        if url:
            folium.TileLayer(tiles=url, attr='GEE', name='💧 Eau (NDWI)', overlay=True, opacity=0.8, show=True).add_to(m)

    if show_ndvi:
        url = get_ndvi_tile_url(lat, lon, start, end, cloud) 
        if url:
            folium.TileLayer(tiles=url, attr='GEE', name='🌿 Végétation', overlay=True, opacity=0.6, show=False).add_to(m)

    # 5. Dessin du Rectangle d'analyse (Preuve de l'AOI)
    folium.Rectangle(
        bounds=bbox_folium,
        color="#c1272d", # Rouge Maroc
        weight=2,
        fill=True,
        fill_opacity=0.05,
        popup="Zone d'analyse Sentinel-2 (AOI)"
    ).add_to(m)

    # 6. Marqueur du barrage
    folium.Marker(
        [lat, lon], 
        popup=f"<b>{row.get('barrage', 'Barrage')}</b>",
        icon=folium.Icon(color='blue', icon='tint')
    ).add_to(m)

    # Ajustement automatique de la vue
    m.fit_bounds(bbox_folium)
    
    # Contrôles
    folium.LayerControl(position='topright').add_to(m)
    plugins.Fullscreen().add_to(m)

    return m 