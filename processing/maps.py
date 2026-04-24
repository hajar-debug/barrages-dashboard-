import folium
from folium import plugins
import ee 

def build_map(lat, lon, row, start, end, cloud, show_ndwi, show_ndvi, show_rgb, show_ndti, radius=5000):
    # ── 1. ZONE D'INTÉRÊT (BBOX) ──
    # On définit une zone d'analyse autour du barrage
    delta = 0.09 if radius > 12000 else 0.06
    bbox_folium = [[lat - delta, lon - delta], [lat + delta, lon + delta]]
    
    # 2. Imports locaux des fonctions de tuiles
    from processing.indices import get_ndwi_tile_url, get_ndvi_tile_url, get_rgb_tile_url, get_ndti_tile_url

    # 3. Initialisation de la carte Folium
    m = folium.Map(
        location=[lat, lon],
        zoom_start=12 if radius < 6000 else 10, 
        tiles=None,
    )

    # ── 4. FONDS DE CARTE ──
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attr='Google Satellite', name='🛰️ Satellite (Google)', overlay=False
    ).add_to(m)

    folium.TileLayer(
        tiles='OpenStreetMap', name='🗺️ Plan (OSM)', overlay=False
    ).add_to(m)

    # ── 5. COUCHES ANALYTIQUES SENTINEL-2 (GEE) ──
    if show_ndti:
        url = get_ndti_tile_url(lat, lon, start, end, cloud) 
        if url:
            folium.TileLayer(tiles=url, attr='GEE', name='🌫️ Turbidité', overlay=True, opacity=0.7, show=False).add_to(m)

    if show_ndwi:
        url = get_ndwi_tile_url(lat, lon, start, end, cloud) 
        if url:
            folium.TileLayer(tiles=url, attr='GEE', name='💧 Surface en Eau', overlay=True, opacity=0.8, show=True).add_to(m)

    if show_ndvi:
        url = get_ndvi_tile_url(lat, lon, start, end, cloud) 
        if url:
            folium.TileLayer(tiles=url, attr='GEE', name='🌿 Végétation', overlay=True, opacity=0.6, show=False).add_to(m)

    # ── 6. MARQUEUR ET EMPRISE ──
    # Rectangle de l'emprise Sentinel
    folium.Rectangle(
        bounds=bbox_folium,
        color="#c1272d",
        weight=2,
        fill=True,
        fill_opacity=0.05,
        popup="Emprise de l'analyse Sentinel-2"
    ).add_to(m)

    # Marqueur du barrage
    nom_barrage = row.get('barrage', 'Barrage')
    folium.Marker(
        [lat, lon], 
        popup=f"<b>{nom_barrage}</b><br>Capacité: {row.get('capacite', '-')} Mm³",
        icon=folium.Icon(color='darkblue', icon='info-sign')
    ).add_to(m)

    # ── 7. OUTILS ET INTERFACE ──
    folium.LayerControl(position='topright', collapsed=False).add_to(m)
    plugins.Fullscreen().add_to(m)
    
    # Ajuster la vue automatiquement
    m.fit_bounds(bbox_folium)

    return m