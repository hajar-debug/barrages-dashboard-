import folium
from folium import plugins
import ee  
import geemap.foliumap as geemap

def build_map(lat, lon, row, start, end, cloud, show_ndwi, show_ndvi, show_rgb, show_ndti):
    # AUGMENTER ICI AUSSI À 5000
    roi = ee.Geometry.Point([lon, lat]).buffer(5000)
    
    # Ajout de get_ndti_tile_url dans l'import
    from processing.indices import get_ndwi_tile_url, get_ndvi_tile_url, get_rgb_tile_url, get_ndti_tile_url

    m = folium.Map(
        location=[lat, lon],
        zoom_start=13,
        tiles=None,
    )

    # ── 1. FONDS DE CARTE (Multi-sources) ─────────────────────────────
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

    # ── 2. COUCHES ANALYTIQUES (Optimisées) ─────────────────────────────
    
    # --- COUCHE NDTI (Turbidité / Envasement) --- AJOUTÉ
    if show_ndti:
        url = get_ndti_tile_url(lat, lon, start, end, cloud_pct)
        if url:
            folium.TileLayer(
                tiles=url,
                attr='GEE',
                name='🌫️ Indice NDTI (Turbidité)',
                overlay=True,
                opacity=0.7,
                show=False # Désactivé par défaut pour ne pas surcharger
            ).add_to(m)

    if show_ndwi:
        url = get_ndwi_tile_url(lat, lon, start, end, cloud_pct)
        if url:
            folium.TileLayer(
                tiles=url,
                attr='GEE',
                name='💧 Indice NDWI (Eau)',
                overlay=True,
                opacity=0.7,
                show=True 
            ).add_to(m)

    if show_ndvi:
        url = get_ndvi_tile_url(lat, lon, start, end, cloud_pct)
        if url:
            folium.TileLayer(
                tiles=url,
                attr='GEE',
                name='🌿 Indice NDVI (Végétation)',
                overlay=True,
                opacity=0.6,
                show=False 
            ).add_to(m)

    # ── 3. INTERFACE ──────────────────────────────────────────────────────
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