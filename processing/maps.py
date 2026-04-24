import folium
from folium import plugins
import ee 
import geopandas as gpd

def build_map(lat, lon, row, start, end, cloud, show_ndwi, show_ndvi, show_rgb, show_ndti, radius=5000):
    # ── 1. ZONE D'INTÉRÊT (RECTANGLE / BBOX) ───────────────────────────
    # On transforme le radius en degrés approximatifs pour créer un rectangle
    # 0.01 degré ~ 1.1km. On adapte selon le barrage.
    delta = 0.09 if radius > 12000 else 0.06
    
    # Géométrie pour Google Earth Engine (Rectangle)
    roi = ee.Geometry.Rectangle([lon - delta, lat - delta, lon + delta, lat + delta])
    
    # Coordonnées pour l'affichage Folium (Bbox)
    bbox_folium = [[lat - delta, lon - delta], [lat + delta, lon + delta]]
    
    # 2. Imports locaux
    from processing.indices import get_ndwi_tile_url, get_ndvi_tile_url, get_rgb_tile_url, get_ndti_tile_url

    # 3. Initialisation de la carte
    m = folium.Map(
        location=[lat, lon],
        zoom_start=12 if radius < 6000 else 10, 
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
        folium.GeoJson(
            "Data/communes.geojson",
            name="🏡 Limites Communales",
            style_function=lambda x: {'fillColor': 'none', 'color': '#7f8c8d', 'weight': 1, 'dashArray': '4, 4'},
            control=True
        ).add_to(m)

        folium.GeoJson(
            "Data/provinces.geojson",
            name="🏢 Limites Provinciales",
            style_function=lambda x: {'fillColor': 'none', 'color': '#c1272d', 'weight': 2},
            control=True
        ).add_to(m)
    except Exception as e:
        print(f"Note: Couches SIG non chargées : {e}")

    # ── 3. COUCHES ANALYTIQUES GEE ─────────────────────────────────────
    # Note : On passe maintenant la 'roi' rectangulaire aux fonctions
    
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

    # ── 4. TRACÉ DU RECTANGLE DE RECHERCHE ────────────────────────────
    folium.Rectangle(
        bounds=bbox_folium,
        color="#c1272d",
        weight=2,
        fill=True,
        fill_opacity=0.05,
        popup="Emprise de l'analyse Sentinel-2"
    ).add_to(m)

    # ── 5. INTERFACE & TOOLS ──────────────────────────────────────────
    folium.LayerControl(position='topright', collapsed=False).add_to(m)
    plugins.Fullscreen().add_to(m)
    plugins.MeasureControl(position='bottomleft').add_to(m)
    
    nom = row.get('barrage', 'Barrage')
    folium.Marker(
        [lat, lon], 
        popup=f"<b>{nom}</b><br>Capacité: {row.get('capacite', '-')} Mm³",
        icon=folium.Icon(color='darkblue', icon='info-sign')
    ).add_to(m)

    # Ajuster la vue automatiquement sur le rectangle
    m.fit_bounds(bbox_folium)

    return m