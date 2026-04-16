import folium
from folium import plugins
from processing.indices import get_ndwi_tile_url, get_ndvi_tile_url, get_rgb_tile_url


def build_map(lat, lon, row, start, end, cloud_pct=20,
              show_ndwi=True, show_ndvi=True, show_rgb=False):
    """
    Construit une carte Folium centrée sur le barrage avec :
    - Marker du barrage
    - Buffer 5 km
    - Couches GEE (NDWI, NDVI, RGB) optionnelles
    - Contrôle des couches
    """
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
        name="🌑 Dark",
        max_zoom=19,
    ).add_to(m)

    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri WorldImagery",
        name="🛰 Satellite",
        max_zoom=19,
    ).add_to(m)

    folium.TileLayer(
        tiles="OpenStreetMap",
        name="🗺 OSM",
    ).add_to(m)

    # ── Buffer 5 km ───────────────────────────────────────────────────────────
    folium.Circle(
        location=[lat, lon],
        radius=5000,
        color="#00c9ff",
        weight=1.5,
        fill=True,
        fill_color="#00c9ff",
        fill_opacity=0.04,
        tooltip="Zone d'analyse (5 km)",
        name="📏 Buffer 5 km",
    ).add_to(m)

    # ── Couches GEE ───────────────────────────────────────────────────────────
    if show_rgb:
        rgb_url = get_rgb_tile_url(lat, lon, start, end, cloud_pct)
        if rgb_url:
            folium.TileLayer(
                tiles=rgb_url,
                attr="Google Earth Engine · Sentinel-2 RGB",
                name="🎨 RGB Satellite (S2)",
                overlay=True,
                opacity=0.85,
            ).add_to(m)

    if show_ndwi:
        ndwi_url = get_ndwi_tile_url(lat, lon, start, end, cloud_pct)
        if ndwi_url:
            folium.TileLayer(
                tiles=ndwi_url,
                attr="Google Earth Engine · NDWI",
                name="💧 NDWI (indice eau)",
                overlay=True,
                opacity=0.7,
            ).add_to(m)

    if show_ndvi:
        ndvi_url = get_ndvi_tile_url(lat, lon, start, end, cloud_pct)
        if ndvi_url:
            folium.TileLayer(
                tiles=ndvi_url,
                attr="Google Earth Engine · NDVI",
                name="🌿 NDVI (végétation)",
                overlay=True,
                opacity=0.7,
            ).add_to(m)

    # ── Marker barrage ────────────────────────────────────────────────────────
    nom     = row.get("nom", "Barrage")
    cap     = row.get("السعة (Mm3)", "—")
    region  = row.get("Nom_Region", "—")
    agence  = row.get("الوكالة", "—")
    usage   = row.get("الإستعمالات", "—")

    popup_html = f"""
    <div style="font-family:sans-serif; min-width:200px;">
        <div style="background:#0a0e1a; color:#00c9ff; padding:8px 12px;
                    font-weight:700; font-size:0.95rem; border-radius:6px 6px 0 0;">
            💧 {nom}
        </div>
        <div style="padding:10px 12px; background:#111827; border-radius:0 0 6px 6px;">
            <table style="width:100%; font-size:0.8rem; color:#e8edf5; border-collapse:collapse;">
                <tr><td style="color:#6b7fa3; padding:3px 0;">Capacité</td><td>{cap} Mm³</td></tr>
                <tr><td style="color:#6b7fa3; padding:3px 0;">Région</td><td>{region}</td></tr>
                <tr><td style="color:#6b7fa3; padding:3px 0;">Agence</td><td>{agence}</td></tr>
                <tr><td style="color:#6b7fa3; padding:3px 0;">Usages</td><td style="direction:rtl;">{usage}</td></tr>
            </table>
        </div>
    </div>
    """

    folium.Marker(
        location=[lat, lon],
        popup=folium.Popup(popup_html, max_width=280),
        tooltip=nom,
        icon=folium.Icon(color="blue", icon="tint", prefix="fa"),
    ).add_to(m)

    # ── Mini-carte + plugins ──────────────────────────────────────────────────
    plugins.MiniMap(toggle_display=True, tile_layer="CartoDB dark_matter").add_to(m)
    plugins.Fullscreen(position="topleft").add_to(m)
    plugins.MousePosition().add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)

    return m