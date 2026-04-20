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
    /* Fond de page blanc/gris très clair */
    [data-testid="stAppViewContainer"] {
        background-color: #ffffff !important;
        color: #1a1a1a !important;
    }

    /* Sidebar claire */
    [data-testid="stSidebar"] {
        background-color: #f8f9fa !important;
    }

    /* Header Design Institutionnel */
    .dash-title {
        font-family: 'Inter', sans-serif;
        font-size: 2.8rem;
        font-weight: 800;
        color: #1a4a7c; /* Bleu profond */
        border-bottom: 3px solid #c1272d; /* Ligne rouge Maroc */
        padding-bottom: 10px;
    }

    /* Note d'Expert Style "Maroc Excellence" */
    .expert-note {
        background: #fff5f5;
        border-right: 5px solid #148337; /* Vert Maroc */
        border-left: 5px solid #c1272d;  /* Rouge Maroc */
        padding: 20px;
        border-radius: 10px;
        margin: 20px 0;
        color: #1a4a7c;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }

    /* Métriques claires */
    [data-testid="metric-container"] {
        background: #ffffff !important;
        border: 1px solid #e0e0e0 !important;
        border-radius: 10px !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
        color: #1a4a7c !important;
    }
</style>
""", unsafe_allow_html=True)
# ── Init GEE ──
try:
    init_gee()
except Exception as e:
    st.error(f"Erreur GEE : {e}")

# ── LOAD DATA ──
@st.cache_data
def load_barrages():
    df_load = pd.read_csv("Data/barrages.csv")
    # Cette ligne est MAGIQUE : elle nettoie tous les noms de colonnes
    df_load.columns = df_load.columns.str.strip().str.lower() 
    return df_load

df = load_barrages()

# ── DICTIONNAIRE DE RÉPLIQUES (LIGNE 87) ──
expert_facts = {
    "AL WAHDA": "Deuxième plus grand barrage d'Afrique, pilier de la régulation du Sebou.",
    "OUED EL MAKHAZINE": "Infrastructure stratégique pour la sécurité alimentaire du Gharb.",
    "S.M.B ABDELLAH": "Garant de l'approvisionnement en eau potable de l'axe Rabat-Casablanca.",
    "DAR KHROUFA": "Ouvrage de nouvelle génération pour le développement agricole du Loukkos.",
    "BIN EL OUIDANE": "Monument de l'hydroélectricité marocaine dans le Haut Atlas.",
    "MOULAY ABDELLAH": "Ressource vitale pour le stress hydrique de la région Souss-Massa.",
    "SIDI EL MAHJOUB": "Point d'eau crucial pour la résilience des zones arides du Sud."
} # <--- VÉRIFIE QUE CETTE ACCOLADE EST BIEN LÀ

# ── Sidebar ──
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding: 10px 0;'>
        <div style='font-size:2.5rem;'>💧</div>
        <div style='font-family:Syne,sans-serif; font-weight:800; color:#00c9ff;'>BARRAGES MAROC</div>
    </div>
    """, unsafe_allow_html=True)

    if not df.empty:
        st.markdown('<div class="section-title">🏞 Sélection</div>', unsafe_allow_html=True)
        barrage_list = df["barrage"].dropna().unique().tolist()
        choice = st.selectbox("Choisissez un barrage :", barrage_list, label_visibility="collapsed")
        # Ajoute ces deux lignes ici :
        row = df[df["barrage"] == choice].iloc[0]
        lat, lon = float(row["lat"]), float(row["lon"])
# --- MINI-CARTE DE SITUATION (FOND CLAIR) ---
        st.write("📍 **Localisation nationale**")
        fig_loc = go.Figure(go.Scattermapbox(
            lat=[lat], lon=[lon],
            mode='markers',
            marker=go.scattermapbox.Marker(size=14, color='#c1272d'),
            text=[choice]
        ))
        fig_loc.update_layout(
            mapbox_style="carto-positron", # FOND CLAIR ET VISIBLE
            mapbox=dict(center=dict(lat=28.5, lon=-9.5), zoom=3.2),
            margin={"r":0,"t":0,"l":0,"b":0}, height=250,
            paper_bgcolor="white", 
            plot_bgcolor="white"
        )
        st.plotly_chart(fig_loc, use_container_width=True, config={'displayModeBar': False})

        st.markdown('<div class="section-title">📅 Période</div>', unsafe_allow_html=True)
        start_date = st.date_input("Début", value=pd.to_datetime("2020-01-01"))
        end_date = st.date_input("Fin", value=pd.to_datetime("2026-04-17"))

        st.markdown('<div class="section-title">☁️ Filtre nuages</div>', unsafe_allow_html=True)
        cloud_pct = st.slider("% nuages max", 0, 100, 20)

        st.markdown('<div class="section-title">🗺 Couches carte</div>', unsafe_allow_html=True)
        show_ndwi  = st.checkbox("💧 NDWI (Eau)", value=True)
        show_ndti  = st.checkbox("🌫️ NDTI (Turbidité)", value=True)
        show_ndvi  = st.checkbox("🌿 NDVI (Végétation)", value=True)
        show_rgb   = st.checkbox("📷 Satellite RGB", value=False)
# ── MAIN INTERFACE ──
if not df.empty:
    start_str = start_date.strftime("2020-01-01") # <-- Correct !
    end_str = end_date.strftime("2026-04-17")
    
    # Header Expert
    st.markdown(f"<div class='dash-title'>Barrage {choice}</div>", unsafe_allow_html=True)
    st.markdown(f"**Bassin Versant :** {row['bassin']} | **Province :** {row['nom_provin']}")
    # --- AFFICHAGE DE LA RÉPLIQUE ---
    fact = expert_facts.get(choice.upper(), "Infrastructure clé pour la stratégie nationale de l'eau.")
    st.markdown(f"""
    <div class="expert-note">
        <span style="color:#00c9ff; font-weight:bold;">💡 ANALYSE STRATÉGIQUE</span><br>
        {fact}<br>
        <small style="color:#6b7fa3;">Mis en service en {row['annee']} | Capacité : {row['capacite']} Mm³ | Usage : {row['usage']}</small>
    </div>
    """, unsafe_allow_html=True)    
# ── Configuration du Buffer Dynamique ──
BUFFER_CONFIG = {
    "Al Wahda": 15000,
    "Oued El Makhazine": 15000,
    "Dar Khroufa": 7000,
    "S.M.B Abdellah": 7000,
    "Moulay Abdellah": 5000,
    "Sidi El Mahjoub": 3000
}
DEFAULT_BUFFER = 5000
current_radius = BUFFER_CONFIG.get(choice, DEFAULT_BUFFER)

# ── Extraction données ──
if not df.empty:
    row = df[df["barrage"] == choice].iloc[0]
    lat, lon = float(row["lat"]), float(row["lon"])
    start_str, end_str = start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")

    # ── Header ──
    st.markdown(f"""
    <div style='display:flex; justify-content:space-between; align-items:flex-end;'>
        <div>
            <div class='dash-title'>سد {row.get('barrage', choice)}</div>
            <div class='dash-sub'>{row.get('nom_region','—')} · {row.get('nom_provin','—')} · {row.get('nom_commun','—')}</div>
        </div>
        <div style='color:var(--muted); font-size:0.8rem;'>{lat:.4f}°N | {lon:.4f}°E | ROI: {current_radius/1000}km</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    # ── Corps ──
    col_img, col_txt = st.columns([1.5, 1])
    with col_img:
        if "image_url" in row and pd.notna(row["image_url"]):
            st.image(row["image_url"], use_container_width=True)
        else:
            st.info("📸 Image non disponible")

    with col_txt:
        st.subheader("🔍 Détails techniques")
        st.markdown(f"""
        **📍 Région :** {row.get('nom_region', '—')}  
        **🏢 Province :** {row.get('nom_provin', '—')}  
        **🏡 Commune :** {row.get('nom_commun', '—')}  
        **🌊 Bassin :** {row.get('bassin', '—')}  
        **📏 Capacité :** {row.get('capacite', '—')} Mm³  
        **💡 Usages :** {row.get('usage', '—')}
        """)

    # ── Tabs ──
    tab1, tab2, tab3, tab4 = st.tabs(["🗺 CARTE", "📊 ANALYSES SPECTRALES", "⚠️ RISQUES", "📄 RAPPORT"])

    with tab1:
        from streamlit_folium import st_folium
        m = build_map(
            lat, lon, row, start_str, end_str, 
            cloud_pct, show_ndwi, show_ndvi, show_rgb, show_ndti, radius=current_radius
        )
        st_folium(m, width='stretch') 

    with tab2:
        from processing.indices import get_metrics, water_surface, get_timeseries, get_water_surface_area, get_climate_data
        
        with st.spinner("Calcul GEE en cours..."):
            metrics = get_metrics(lat, lon, start_str, end_str, cloud_pct, radius=5000)
            water = water_surface(lat, lon, start_str, end_str, cloud_pct, radius=5000)
            water = water_surface(lat, lon, start_str, end_str, cloud_pct)

        # Nouveau design des colonnes de métriques
        c1, c2, c3, c4 = st.columns(4) 
        with c1:
            st.metric(label="💧 Indice d'Eau", value=f"{ndwi:.3f}" if ndwi else "N/A", help="NDWI : Plus il est haut, plus la présence d'eau est confirmée.")
        with c2:
            st.metric(label="🌫️ Turbidité", value=f"{ndti:.3f}" if ndti else "N/A", help="NDTI : Mesure la clarté de l'eau.")
        with c3:
            st.metric(label="🌿 Santé Berges", value=f"{ndvi:.3f}" if ndvi else "N/A", help="NDVI : État de la végétation environnante.")
        with c4:
            st.metric(label="📐 Surface Estimée", value=f"{water:.2f} km²" if water else "N/A")
        st.markdown("### 📈 Évolution Temporelle")
        ts = get_timeseries(lat, lon, start_str, end_str, cloud_pct, radius=5000)
        fig = None 
        
        if ts is not None and not ts.empty:
            fig = px.line(
                ts, 
                x="date", 
                y=["NDWI", "Turbidité"], 
                template="plotly_dark",
                color_discrete_map={"NDWI": "#00c9ff", "Turbidité": "#ffa500"}
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("📊 Aucune donnée historique disponible.")

        st.markdown("### 🛰️ Bilan de Surface (Analyse Comparative)")
        col_a, col_b = st.columns(2)
        
        with col_a:
            surface_initiale = get_water_surface_area(lat, lon, "2020-01-01", cloud_pct)
            st.metric("Surface Janvier 2020", f"{surface_initiale:.2f} km²" if surface_initiale else "N/A")
        
        with col_b:
            surface_actuelle = water if water else 0
            delta = surface_actuelle - (surface_initiale if surface_initiale else 0)
            st.metric("Surface Actuelle", f"{surface_actuelle:.2f} km²", delta=f"{delta:.2f} km²")

        if surface_actuelle < (surface_initiale if surface_initiale else 0):
            st.warning(f"⚠️ Perte de surface liquide de {abs(delta):.2f} km² par rapport à 2020.")

        st.markdown("### 🌡️ Contexte Climatique")
        temp_actuelle = get_climate_data(lat, lon, end_str)
        climat_df = pd.DataFrame({
            "Indicateur": ["Température Moyenne", "Évapotranspiration (est.)", "État du Ciel"],
            "Valeur": [f"{temp_actuelle:.1f} °C", "4.5 mm/jour", "Dégagé" if cloud_pct < 20 else "Nuageux"],
            "Impact": ["Normal", "Risque de perte d'eau", "Optimale"]
        })
        st.table(climat_df)

    with tab3:
        from processing.analysis import compute_risk, generate_alerts
        rl, rs = compute_risk(ndwi, ndvi, ndti)
        al = generate_alerts(ndwi, ndvi, water, ndti)
        
        st.subheader(f"État du réservoir : {rl}")
        st.progress(rs / 100)
        
        st.subheader("🌊 Alerte Prédictive Inondation")
        flood_risk = (ndwi + 0.1) * 100 if ndwi else 0
        if flood_risk > 80:
            st.error(f"🚨 RISQUE CRITIQUE ({flood_risk:.1f}%) : Capacité maximale atteinte.")
        elif flood_risk > 50:
            st.warning(f"⚠️ VIGILANCE ({flood_risk:.1f}%) : Niveau élevé.")
        else:
            st.success(f"✅ RISQUE FAIBLE ({flood_risk:.1f}%)")

        st.markdown("### 🏥 Bilan de Santé du Réservoir")
        h1, h2, h3 = st.columns(3)
        with h1:
            st.write("**💧 Remplissage**")
            # On ajoute "ndwi is not None" pour éviter le crash
            if ndwi is not None and ndwi > 0.15: 
                st.success("Excellent")
            elif ndwi is not None:
                st.error("Critique")
            else:
                st.warning("Indisponible")

        with h2:
            st.write("**🌫️ Qualité**")
            if ndti is not None and ndti < 0.05: 
                st.success("Claire")
            elif ndti is not None:
                st.warning("Turbide")
            else:
                st.warning("Indisponible")
        with h3:
            st.write("**🌿 Berges**")
            # On vérifie si ndvi existe AVANT de comparer
            if ndvi is not None:
                if ndvi > 0.25: 
                    st.success("Stable")
                else: 
                    st.warning("Érosion / Faible")
            else:
                st.info("Donnée N/A")

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

        if 'pdf_bytes' in locals() and pdf_bytes is not None:
            st.download_button(
                label="📥 Télécharger le Rapport PDF",
                data=pdf_bytes,
                file_name=f"Rapport_{choice}.pdf",
                mime="application/pdf"
            )
        else:
            # ICI : Il faut 1 tabulation (ou 4 espaces) de plus que le "else"
            st.warning("⚠️ Le rapport PDF n'est pas disponible car les données GEE sont absentes (N/A).")
        
        # Cette ligne revient au niveau du "if" initial
        st.info(interpretation if interpretation else "Sélectionnez une période.")
