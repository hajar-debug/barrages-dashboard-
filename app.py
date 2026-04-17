import streamlit as st
import pandas as pd
from processing.gee_init import init_gee

st.set_page_config(
    page_title="Barrages Maroc | Dashboard SIG",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CSS Pro ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

:root {
    --bg:       #0a0e1a;
    --surface:  #111827;
    --card:     #1a2235;
    --border:   #1e3a5f;
    --accent:   #00c9ff;
    --accent2:  #0066ff;
    --green:    #00e5a0;
    --orange:   #ff9500;
    --red:      #ff3b5c;
    --text:     #e8edf5;
    --muted:    #6b7fa3;
}

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: var(--bg);
    color: var(--text);
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1526 0%, #0a0e1a 100%);
    border-right: 1px solid var(--border);
}

header[data-testid="stHeader"] { background: transparent; }

[data-testid="metric-container"] {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 16px 20px;
}

.dash-title {
    font-family: 'Syne', sans-serif;
    font-size: 2rem;
    font-weight: 800;
    background: linear-gradient(90deg, #00c9ff, #0066ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: -0.03em;
    margin-bottom: 0;
}

.dash-sub {
    font-size: 0.85rem;
    color: var(--muted);
    font-weight: 300;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-top: 2px;
}

.section-title {
    font-family: 'Syne', sans-serif;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: var(--accent);
    margin: 24px 0 10px 0;
}

.info-panel {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 20px;
    height: 100%;
}

.info-row {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    padding: 8px 0;
    border-bottom: 1px solid rgba(30,58,95,0.5);
    font-size: 0.82rem;
}
.info-row:last-child { border-bottom: none; }
.info-label { color: var(--muted); font-weight: 400; flex: 0 0 45%; }
.info-value { color: var(--text); font-weight: 500; text-align: right; flex: 0 0 52%; }

.risk-badge {
    display: inline-block;
    padding: 4px 14px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
    font-family: 'Syne', sans-serif;
}
.risk-green  { background: rgba(0,229,160,0.15); color: #00e5a0; border: 1px solid rgba(0,229,160,0.3); }
.risk-orange { background: rgba(255,149,0,0.15);  color: #ff9500; border: 1px solid rgba(255,149,0,0.3); }
.risk-red    { background: rgba(255,59,92,0.15);   color: #ff3b5c; border: 1px solid rgba(255,59,92,0.3); }

.alert-box {
    background: rgba(255,59,92,0.08);
    border: 1px solid rgba(255,59,92,0.25);
    border-radius: 10px;
    padding: 12px 16px;
    font-size: 0.83rem;
    color: #ff8fa3;
    margin-top: 8px;
}

.cap-bar-bg {
    background: rgba(255,255,255,0.06);
    border-radius: 6px;
    height: 8px;
    margin-top: 4px;
    overflow: hidden;
}
.cap-bar-fill {
    height: 8px;
    border-radius: 6px;
    background: linear-gradient(90deg, #00c9ff, #0066ff);
}
</style>
""", unsafe_allow_html=True)

# ── Init GEE ───────────────────────────────────────────────────────────────────
init_gee()

# ── Load Data ──────────────────────────────────────────────────────────────────
@st.cache_data
def load_barrages():
    df = pd.read_csv("Data/barrages.csv")
    df.columns = df.columns.str.strip().str.lower()
    return df

df = load_barrages()

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding: 20px 0 10px 0;'>
        <div style='font-size:2.5rem;'>💧</div>
        <div style='font-family:Syne,sans-serif; font-weight:800; font-size:1.1rem;
                    background:linear-gradient(90deg,#00c9ff,#0066ff);
                    -webkit-background-clip:text; -webkit-text-fill-color:transparent;'>
            BARRAGES MAROC
        </div>
        <div style='font-size:0.7rem; color:#6b7fa3; letter-spacing:0.1em; margin-top:2px;'>
            SYSTÈME DE SURVEILLANCE SIG
        </div>
    </div>
    <hr style='border-color:#1e3a5f; margin: 12px 0;'>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">🏞 Sélection</div>', unsafe_allow_html=True)
    # UN SEUL SELECTBOX ICI
    choice = st.selectbox("Choisissez un barrage :", df["barrage"].dropna().unique().tolist())

    st.markdown('<div class="section-title">📅 Période d\'analyse</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Début", value=pd.to_datetime("2020-01-01"),
                                    min_value=pd.to_datetime("2017-01-01"),
                                    label_visibility="collapsed")
    with col2:
        end_date = st.date_input("Fin", value=pd.to_datetime("2025-12-31"),
                                  label_visibility="collapsed")

    st.markdown('<div class="section-title">☁️ Filtre nuages</div>', unsafe_allow_html=True)
    cloud_pct = st.slider("% nuages max", 0, 50, 20, label_visibility="collapsed")

    st.markdown('<div class="section-title">🗺 Couches carte</div>', unsafe_allow_html=True)
    show_ndwi  = st.checkbox("NDWI (eau)", value=True)
    show_ndvi  = st.checkbox("NDVI (végétation)", value=True)
    show_rgb   = st.checkbox("RGB Satellite", value=False)

# ── Get selected barrage row ───────────────────────────────────────────────────
row = df[df["barrage"] == choice].iloc[0]
lat = float(row["lat"])
lon = float(row["lon"])
start_str = start_date.strftime("%Y-%m-%d")
end_str   = end_date.strftime("%Y-%m-%d")

# ── Header & Caractéristiques rapides ──────────────────────────────────────────
st.markdown(f"""
<div style='display:flex; justify-content:space-between; align-items:flex-end; margin-bottom:20px;'>
    <div>
        <div class='dash-title'>سد {row.get('barrage', choice)}</div>
        <div class='dash-sub'>
            {row.get('nom_region','—')} &nbsp;·&nbsp;
            {row.get('nom_provin','—')} &nbsp;·&nbsp;
            {row.get('nom_commun','—')}
        </div>
    </div>
    <div style='text-align:right; font-size:0.75rem; color:#3d5278;'>
        {lat:.4f}°N &nbsp; {lon:.4f}°E
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")
col_img, col_txt = st.columns([1.5, 1])

with col_img:
    if "image_url" in row and pd.notna(row["image_url"]):
        st.image(row["image_url"], use_container_width=True, caption=f"Barrage {choice}")
    else:
        st.warning("📸 Image non disponible")

with col_txt:
    st.subheader("🔍 Détails techniques")
    st.write(f"**🌊 Bassin :** {row.get('bassin', '—')}")
    st.write(f"**📅 Mise en service :** {int(float(row.get('annee',0)))} ")
    st.write(f"**📏 Capacité :** {row.get('capacite', '—')} Mm³")
    st.write(f"**💡 Usages :** {row.get('usage', '—')}")

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["🗺 CARTE", "📊 ANALYSES", "⚠️ RISQUES", "📄 RAPPORT"])

with tab1:
    map_col, info_col = st.columns([3, 1])
    with map_col:
        from processing.maps import build_map
        from streamlit_folium import st_folium
        m = build_map(lat, lon, row, start_str, end_str, cloud_pct,
                      show_ndwi=show_ndwi, show_ndvi=show_ndvi, show_rgb=show_rgb)
        st_folium(m, width=None, height=580, returned_objects=[])

    with info_col:
        cap = float(row.get("capacite", 0) or 0)
        max_cap = df["capacite"].astype(float).max()
        pct = int((cap / max_cap * 100)) if max_cap else 0

        st.markdown(f"""
        <div class="info-panel">
            <div style="font-family:Syne,sans-serif; font-weight:700; font-size:0.95rem; color:#00c9ff; margin-bottom:14px;">📋 FICHE BARRAGE</div>
            <div class="info-row"><span class="info-label">Capacité</span><span class="info-value">{cap:.0f} Mm³</span></div>
            <div class="cap-bar-bg"><div class="cap-bar-fill" style="width:{pct}%;"></div></div>
            <div class="info-row"><span class="info-label">Région</span><span class="info-value">{row.get('nom_region','—')}</span></div>
            <div class="info-row"><span class="info-label">Province</span><span class="info-value">{row.get('nom_provin','—')}</span></div>
            <div class="info-row"><span class="info-label">Commune</span><span class="info-value">{row.get('nom_commun','—')}</span></div>
        </div>
        """, unsafe_allow_html=True)

with tab2:
    from processing.indices import get_ndwi_mean, get_ndvi_mean, water_surface, get_timeseries
    with st.spinner("Calcul des indices GEE…"):
        ndwi = get_ndwi_mean(lat, lon, start_str, end_str, cloud_pct)
        ndvi = get_ndvi_mean(lat, lon, start_str, end_str, cloud_pct)
        water = water_surface(lat, lon, start_str, end_str, cloud_pct)

    c1, c2, c3 = st.columns(3)
    c1.metric("💧 NDWI moyen", f"{ndwi:.3f}" if ndwi else "N/A")
    c2.metric("🌿 NDVI moyen", f"{ndvi:.3f}" if ndvi else "N/A")
    c3.metric("📐 Surface eau", f"{water:.2f} km²" if water else "N/A")

    ts = get_timeseries(lat, lon, start_str, end_str, cloud_pct)
    if ts is not None and not ts.empty:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        fig = make_subplots(rows=2, cols=1, subplot_titles=("NDWI", "NDVI"))
        fig.add_trace(go.Scatter(x=ts["date"], y=ts["NDWI"], name="NDWI", fill="tozeroy"), row=1, col=1)
        fig.add_trace(go.Scatter(x=ts["date"], y=ts["NDVI"], name="NDVI", fill="tozeroy"), row=2, col=1)
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    from processing.analysis import compute_risk, generate_alerts
    risk_level, risk_score = compute_risk(ndwi, ndvi)
    alerts = generate_alerts(ndwi, ndvi, water)
    badge_class = {"🟢 Faible": "risk-green", "🟠 Moyen": "risk-orange", "🔴 Critique": "risk-red"}.get(risk_level, "risk-orange")
    
    st.markdown(f'<span class="risk-badge {badge_class}">{risk_level} (Score: {risk_score}/100)</span>', unsafe_allow_html=True)
    for alert in (alerts or ["✅ Aucune alerte"]):
        st.markdown(f'<div class="alert-box">{alert}</div>', unsafe_allow_html=True)
with tab4:
    st.markdown('<div class="section-title">📄 Exportation Rapport</div>', unsafe_allow_html=True)
    from report.report_generator import generate_pdf
    
    if st.button("📥 Générer le rapport PDF", use_container_width=True):
        try:
            with st.spinner("Génération du PDF..."):
                # On passe TOUTES les variables nécessaires
                pdf_output = generate_pdf(
                    barrage_name=choice, 
                    row=row, 
                    ndwi=ndwi, 
                    ndvi=ndvi, 
                    water=water, 
                    risk_level=risk_level, 
                    risk_score=risk_score, 
                    alerts=alerts, 
                    start=start_str, 
                    end=end_str
                )
                
                # Conversion impérative en bytes
                final_pdf = bytes(pdf_output)
                
                st.success("✅ Rapport généré avec succès !")
                st.download_button(
                    label="⬇️ Télécharger le PDF",
                    data=final_pdf,
                    file_name=f"Rapport_{choice}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
        except Exception as e:
            st.error(f"Erreur technique : {e}")
