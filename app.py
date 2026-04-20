import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from processing.gee_init import init_gee
from report.report_generator import generate_pdf
from datetime import datetime
from processing.maps import build_map

st.set_page_config(
    page_title="Barrages Maroc | Dashboard SIG",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CSS Pro ──────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=Inter:wght@300;400;600&display=swap');

    [data-testid="stAppViewContainer"] {
        background-color: #0b0f19;
        background-image: radial-gradient(circle at 2px 2px, #1a2235 1px, transparent 0);
        background-size: 40px 40px;
    }

    .dash-title {
        font-family: 'Syne', sans-serif;
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(90deg, #00c9ff, #ffffff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .expert-note {
        background: linear-gradient(90deg, rgba(0, 201, 255, 0.1), transparent);
        border-left: 5px solid #00c9ff;
        padding: 20px;
        border-radius: 0 15px 15px 0;
        margin: 20px 0;
    }

    [data-testid="metric-container"] {
        background: rgba(23, 30, 48, 0.7) !important;
        border: 1px solid rgba(0, 201, 255, 0.2) !important;
        border-radius: 12px !important;
        backdrop-filter: blur(10px);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }

    .section-title {
        font-family: 'Syne', sans-serif;
        font-size: 0.8rem;
        letter-spacing: 2px;
        text-transform: uppercase;
        color: #00c9ff;
        margin: 25px 0 10px 0;
        border-bottom: 1px solid rgba(0, 201, 255, 0.2);
    }
</style>
""", unsafe_allow_html=True)

# ── Init GEE ──
try:
    init_gee()
except Exception as e:
    st.error(f"Erreur d'initialisation Google Earth Engine : {e}")

# ── LOAD DATA ──
@st.cache_data
def load_barrages():
    df_load = pd.read_csv("Data/barrages.csv")
    df_load.columns = df_load.columns.str.strip() 
    return df_load

df = load_barrages()

# ── DICTIONNAIRE DE RÉPLIQUES ──
expert_facts = {
    "AL WAHDA": "Deuxième plus grand barrage d'Afrique, pilier de la régulation du Sebou.",
    "OUED EL MAKHAZINE": "Infrastructure stratégique pour la sécurité alimentaire du Gharb.",
    "S.M.B ABDELLAH": "Garant de l'approvisionnement en eau potable de l'axe Rabat-Casablanca.",
    "DAR KHROUFA": "Ouvrage de nouvelle génération pour le développement agricole du Loukkos.",
    "BIN EL OUIDANE": "Monument de l'hydroélectricité marocaine dans le Haut Atlas.",
    "MOULAY ABDELLAH": "Ressource vitale pour le stress hydrique de la région Souss-Massa.",
    "SIDI EL MAHJOUB": "Point d'eau crucial pour la résilience des zones arides du Sud."
}

# ── LOGIQUE DE SÉLECTION & SIDEBAR ──
if not df.empty:
    with st.sidebar:
        st.markdown("""
        <div style='text-align:center; padding: 10px 0;'>
            <div style='font-size:2.5rem;'>💧</div>
            <div style='font-family:Syne,sans-serif; font-weight:800; color:#00c9ff;'>BARRAGES MAROC</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="section-title">🏞 Sélection</div>', unsafe_allow_html=True)
        barrage_list = df["Barrage"].dropna().unique().tolist()
        choice = st.selectbox("Choisissez un barrage :", barrage_list, label_visibility="collapsed")

        # Extraction immédiate des données pour la carte de situation
        row = df[df["Barrage"] == choice].iloc[0]
        lat, lon = float(row["Lat"]), float(row["Lon"])

        # --- MINI-CARTE DE SITUATION (SAHARA INCLUS) ---
        st.markdown('<div class="section-title">📍 Situation Nationale</div>', unsafe_allow_html=True)
        fig_loc = go.Figure(go.Scattermapbox(
            lat=[lat], lon=[lon],
            mode='markers',
            marker=go.scattermapbox.Marker(size=14, color='#c1272d'),
            text=[choice]
        ))
        fig_loc.update_layout(
            mapbox_style="carto-darkmatter",
            mapbox=dict(center=dict(lat=28.5, lon=-9.5), zoom=3.5),
            margin={"r":0,"t":0,"l":0,"b":0}, height=250,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig_loc, use_container_width=True, config={'displayModeBar': False})

        st.markdown('<div class="section-title">📅 Période</div>', unsafe_allow_html=True)
        start_date = st.date_input("Début", value=pd.to_datetime("2024-01-01"))
        end_date = st.date_input("Fin", value=datetime.now())

        st.markdown('<div class="section-title">☁️ Filtre nuages</div>', unsafe_allow_html=True)
        cloud_pct = st.slider("% nuages max", 0, 100, 20)

        st.markdown('<div class="section-title">🗺 Couches carte</div>', unsafe_allow_html=True)
        show_ndwi = st.checkbox("💧 NDWI (Eau)", value=True)
        show_ndti = st.checkbox("🌫️ NDTI (Turbidité)", value=True)
        show_ndvi = st.checkbox("🌿 NDVI (Végétation)", value=True)
        show_rgb  = st.checkbox("📷 Satellite RGB", value=False)

    # ── MAIN INTERFACE ──
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    # Buffer Dynamique
    BUFFER_CONFIG = {"AL WAHDA": 15000, "OUED EL MAKHAZINE": 15000, "DAR KHROUFA": 7000}
    current_radius = BUFFER_CONFIG.get(choice.upper(), 5000)
    
    # Header Expert
    st.markdown(f"<div class='dash-title'>Barrage {choice}</div>", unsafe_allow_html=True)
    st.markdown(f"**Bassin Versant :** {row.get('Bassin','—')} | **Province :** {row.get('nom_provin','—')}")

    # --- AFFICHAGE DE LA RÉPLIQUE ---
    fact = expert_facts.get(choice.upper(), "Infrastructure clé pour la stratégie nationale de l'eau.")
    st.markdown(f"""
    <div class="expert-note">
        <span style="color:#00c9ff; font-weight:bold;">💡 ANALYSE STRATÉGIQUE</span><br>
        {fact}<br>
        <small style="color:#6b7fa3;">Mis en service en {row.get('Annee','—')} | Capacité : {row.get('Capacite','—')} Mm³ | Usage : {row.get('Usage','—')}</small>
    </div>
    """, unsafe_allow_html=True)

    # ── Header Localisation ──
    st.markdown(f"""
    <div style='display:flex; justify-content:space-between; align-items:flex-end;'>
        <div>
            <div style='font-family:Syne; font-size:1.5rem; color:#f8fafc;'>Détails Géographiques</div>
            <div style='color:#6b7fa3;'>{row.get('nom_region','—')} · {row.get('nom_commun','—')}</div>
        </div>
        <div style='color:#00c9ff; font-size:0.9rem;'>{lat:.4f}°N | {lon:.4f}°E | Zone d'étude: {current_radius/1000}km</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    # ── Corps ──
    col_img, col_txt = st.columns([1.5, 1])
    with col_img:
        if "Image_URL" in row and pd.notna(row["Image_URL"]):
            st.image(row["Image_URL"], use_container_width=True)
        else:
            st.info("📸 Image non disponible")

    with col_txt:
        st.subheader("🔍 Fiche Technique")
        st.markdown(f"""
        - **Bassin :** {row.get('Bassin', '—')}
        - **Capacité :** {row.get('Capacite', '—')} Mm³
        - **Année :** {row.get('Annee', '—')}
        - **Usage :** {row.get('Usage', '—')}
        """)

    # ── Tabs ──
    tab1, tab2, tab3, tab4 = st.tabs(["🗺 CARTE SIG", "📊 ANALYSE SPECTRALE", "⚠️ RISQUES", "📄 RAPPORT"])

    with tab1:
        from streamlit_folium import st_folium
        m = build_map(lat, lon, row, start_str, end_str, cloud_pct, show_ndwi, show_ndvi, show_rgb, show_ndti, radius=current_radius)
        st_folium(m, width=1400, height=550) 

    with tab2:
        from processing.indices import get_metrics, water_surface, get_timeseries, get_water_surface_area, get_climate_data
        with st.spinner("Calcul GEE en cours..."):
            metrics = get_metrics(lat, lon, start_str, end_str, cloud_pct, radius=current_radius)
            ndwi, ndvi, ndti = metrics['ndwi'], metrics['ndvi'], metrics['ndti']
            water = water_surface(lat, lon, start_str, end_str, cloud_pct, radius=current_radius)

        c1, c2, c3, c4 = st.columns(4) 
        c1.metric("💧 Eau (NDWI)", f"{ndwi:.3f}" if ndwi else "N/A")
        c2.metric("🌫️ Turbidité", f"{ndti:.3f}" if ndti else "N/A")
        c3.metric("🌿 Végétation", f"{ndvi:.3f}" if ndvi else "N/A")
        c4.metric("📐 Surface", f"{water:.2f} km²" if water else "N/A")
        
        st.markdown("### 📈 Évolution Temporelle")
        ts = get_timeseries(lat, lon, start_str, end_str, cloud_pct, radius=current_radius)
        if ts is not None and not ts.empty:
            fig = px.line(ts, x="date", y=["NDWI", "Turbidité"], template="plotly_dark", color_discrete_map={"NDWI": "#00c9ff", "Turbidité": "#ffa500"})
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("📊 Aucune donnée historique.")

    with tab3:
        from processing.analysis import compute_risk, generate_alerts
        rl, rs = compute_risk(ndwi, ndvi, ndti)
        st.subheader(f"État : {rl}")
        st.progress(rs / 100)
        
        flood_risk = (ndwi + 0.1) * 100 if ndwi else 0
        if flood_risk > 80: st.error(f"🚨 RISQUE CRITIQUE ({flood_risk:.1f}%)")
        else: st.success(f"✅ RISQUE FAIBLE ({flood_risk:.1f}%)")

    with tab4:
        st.markdown("### 📄 Analyse Hydrologique & Rapport")
        interpretation = ""
        if ndwi is not None:
            if ndwi > 0.15: 
                interpretation += "✅ **État de l'eau** : Remplissage élevé.\n\n"
            elif ndwi > 0.02:
                interpretation += "⚠️ **État de l'eau** : Niveau moyen.\n\n"
            else:
                interpretation += "🚨 **Alerte** : Sécheresse critique.\n\n"

        if st.button("🏗️ Préparer le rapport PDF"):
            with st.spinner("Génération..."):
                pdf_output = generate_pdf(choice, row, ndwi, ndvi, water, rl, rs, al, start_str, end_str, ndti, fig=fig)
                try:
                    if hasattr(pdf_output, 'output'):
                        pdf_bytes = pdf_output.output(dest='S')
                    elif isinstance(pdf_output, str):
                        pdf_bytes = pdf_output.encode('latin-1')
                    else:
                        pdf_bytes = pdf_output
                except Exception as e:
                    st.error(f"Erreur conversion : {e}")
                    pdf_bytes = None

                if pdf_bytes:
                    st.success("✅ Rapport prêt !")
                    st.download_button(label="📥 Télécharger PDF", data=pdf_bytes, file_name=f"Rapport_{choice}.pdf", mime="application/pdf")
        
        st.info(interpretation if interpretation else "Sélectionnez une période.")
else:
    st.error("Désolé, le fichier de données est introuvable ou vide.")