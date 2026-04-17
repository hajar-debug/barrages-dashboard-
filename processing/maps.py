import folium
from folium import plugins
from processing.indices import get_ndwi_tile_url, get_ndvi_mean, get_ndwi_mean # Assure-toi que ces imports correspondent à tes fonctions

def build_map(lat, lon, row, start, end, cloud_pct=20,
              show_ndwi=True, show_ndvi=True, show_rgb=False):
    """
    Construit une carte Folium centrée sur le barrage avec couches GEE dynamiques.
    """
    # Importation locale des fonctions d'URL pour éviter les conflits
    from processing.indices import get_ndwi_tile_url, get_ndvi_tile_url, get_rgb_tile_url

    m = folium.Map(
        location=[lat, lon],
        zoom_start=12,
        tiles=None,
        control_scale=True,
    )

    # ── Fond de carte ─────────────────────────────────────────────────────────
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB Dark",
        name="🌑 Mode Sombre",
        max_zoom=19,
    ).add_to(m)

    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri WorldImagery",
        name="🛰 Satellite Réel",
        max_zoom=19,
    ).add_to(m)

    # ── Couches GEE (Sentinel-2) ──────────────────────────────────────────────
    if show_rgb:
        rgb_url = get_rgb_tile_url(lat, lon, start, end, cloud_pct)
        if rgb_url:
            folium.TileLayer(
                tiles=rgb_url,
                attr="Sentinel-2 RGB",
                name="🎨 Couleur Naturelle (S2)",
                overlay=True,
                opacity=0.9,
            ).add_to(m)

    if show_ndwi:
        ndwi_url = get_ndwi_tile_url(lat, lon, start, end, cloud_pct)
        if ndwi_url:
            folium.TileLayer(
                tiles=ndwi_url,
                attr="Sentinel-2 NDWI",
                name="💧 Indice Eau (NDWI)",
                overlay=True,
                opacity=0.7,
            ).add_to(m)

    if show_ndvi:
        ndvi_url = get_ndvi_tile_url(lat, lon, start, end, cloud_pct)
        if ndvi_url:
            folium.TileLayer(
                tiles=ndvi_url,
                attr="Sentinel-2 NDVI",
                name="🌿 Indice Végétation (NDVI)",
                overlay=True,
                opacity=0.7,
            ).add_to(m)

    # ── Buffer d'analyse ──────────────────────────────────────────────────────
    folium.Circle(
        location=[lat, lon],
        radius=5000,
        color="#00c9ff",
        weight=1,
        fill=True,
        fill_color="#00c9ff",
        fill_opacity=0.05,
        name="📏 Zone d'étude (5km)"
    ).add_to(m)

    # ── Marker et Popup (CORRIGÉ avec les noms de colonnes simplifiés) ────────
    # On utilise .get() avec les noms nettoyés par app.py (minuscules)
    nom    = row.get("barrage", "Barrage")
    cap    = row.get("capacite", "—")
    region = row.get("nom_region", "—")
    bassin = row.get("bassin", "—")
    usage  = row.get("usage", "—")

    popup_html = f"""
    <div style="font-family:'DM Sans', sans-serif; min-width:220px; background:#0a0e1a; color:white; border-radius:8px; overflow:hidden;">
        <div style="background:linear-gradient(90deg, #00c9ff, #0066ff); padding:10px; font-weight:bold;">
            💧 {nom}
        </div>
        <div style="padding:10px; font-size:12px;">
            <table style="width:100%; border-collapse:collapse;">
                <tr style="border-bottom:1px solid #1e3a5f;"><td style="color:#6b7fa3; py:4px;">Capacité:</td><td><b>{cap} Mm³</b></td></tr>
                <tr style="border-bottom:1px solid #1e3a5f;"><td style="color:#6b7fa3; py:4px;">Région:</td><td>{region}</td></tr>
                <tr style="border-bottom:1px solid #1e3a5f;"><td style="color:#6b7fa3; py:4px;">Bassin:</td><td>{bassin}</td></tr>
                <tr><td style="color:#6b7fa3; py:4px;">Usages:</td><td style="font-size:10px;">{usage}</td></tr>
            </table>
        </div>
    </div>
    """

    folium.Marker(
        location=[lat, lon],
        popup=folium.Popup(popup_html, max_width=300),
        tooltip=f"Cliquez pour voir les détails de {nom}",
        icon=folium.Icon(color="blue", icon="tint", prefix="fa"),
    ).add_to(m)

    # ── Plugins de contrôle ───────────────────────────────────────────────────
    plugins.Fullscreen(position="topleft").add_to(m)
    plugins.MeasureControl(position="bottomleft", primary_length_unit="kilometers").add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)

    return m