import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import geopandas as gpd
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
# ── LOAD DATA ──
@st.cache_data
def load_barrages():
    # 1. Charger le CSV et normaliser
    df_csv = pd.read_csv("Data/barrages.csv")
    df_csv.columns = df_csv.columns.str.strip().str.lower()
    df_csv['barrage_key'] = df_csv['barrage'].astype(str).str.strip().str.lower()
    
    # 2. Charger le GeoJSON et normaliser
    gdf_sig = gpd.read_file("Data/barrages.geojson")
    gdf_sig.columns = gdf_sig.columns.str.strip().str.lower()
    
    # CORRECTION ICI : Bien aligné avec 4 espaces
    if 'barrage' in gdf_sig.columns:
        col_name = 'barrage'
    else:
        col_name = gdf_sig.columns[0]
        
    gdf_sig['barrage_key'] = gdf_sig[col_name].astype(str).str.strip().str.lower()
    
    # 3. Fusion
    df_combined = gdf_sig.merge(df_csv, on="barrage_key", how="inner")
    
    return df_combined

# Change load_combined_data() par load_barrages()
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
        # On utilise barrage_key qui est garantie d'exister après notre load_barrages
        barrage_list = sorted(df["barrage_key"].str.upper().unique().tolist())
        choice_key = st.selectbox("Choisissez un barrage :", barrage_list)
        choice = choice_key.title() # Pour l'affichage propre

        # 2. RÉCUPÉRATION SÉCURISÉE DE LA LIGNE (C'est ici que ça se joue)
        # On cherche la ligne qui correspond au choix
        row = df[df["barrage_key"] == choice_key.lower()].iloc[0]
        
        # On extrait lat/lon avec des noms de secours (lat ou latitude)
        lat = float(row.get('lat', row.get('latitude', 0)))
        lon = float(row.get('lon', row.get('longitude', 0)))
    
        # On donne une valeur par défaut pour que Python ne dise plus "not defined"
        ndwi, ndvi, ndti = None, None, None
        surface_actuelle = 0
        interpretation = ""
        
# --- MINI-CARTE DE SITUATION ---
        st.write("📍 **Localisation nationale**")
        fig_loc = go.Figure(go.Scattermapbox(
            lat=[lat], lon=[lon],
            mode='markers',
            marker=go.scattermapbox.Marker(size=14, color='#c1272d'),
            text=[choice]
        ))
        fig_loc.update_layout(
            mapbox_style="carto-positron", 
            mapbox=dict(center=dict(lat=28.5, lon=-9.5), zoom=3.2),
            margin={"r":0,"t":0,"l":0,"b":0}, 
            height=250
        )

        st.plotly_chart(fig_loc, use_container_width=True, config={'displayModeBar': False})

        st.markdown('<div class="section-title">📅 Période</div>', unsafe_allow_html=True)
        start_date = st.date_input("Début", value=pd.to_datetime("2020-01-01"))
        end_date = st.date_input("Fin", value=pd.to_datetime("2026-04-17"))

        st.markdown('<div class="section-title">☁️ Filtre nuages</div>', unsafe_allow_html=True)
        cloud_pct = st.slider("% nuages max", 0, 50, 20)

        st.markdown('<div class="section-title">🗺 Couches carte</div>', unsafe_allow_html=True)
        show_ndwi = st.checkbox("💧 NDWI (Eau)", value=True)
        show_ndti = st.checkbox("🌫️ NDTI (Turbidité)", value=True)
        show_ndvi = st.checkbox("🌿 NDVI (Végétation)", value=True)
        show_rgb  = st.checkbox("📷 Satellite RGB", value=False)
# ── MAIN INTERFACE ──
if not df.empty:
    start_str = start_date.strftime("%Y-%m-%d") # On utilise le format année-mois-jour
    end_str = end_date.strftime("%Y-%m-%d")
    
    # Header Expert
    st.markdown(f"<div class='dash-title'>Barrage {choice}</div>", unsafe_allow_html=True)
# On récupère les infos de manière sécurisée (si la colonne manque, ça n'affiche pas d'erreur)
    bassin_nom = row.get('bassin', 'Inconnu')
    province_nom = row.get('nom_provin', row.get('province', 'Inconnue'))

    st.markdown(f"### 📍 Localisation")
    st.info(f"**Bassin Versant :** {bassin_nom} | **Province :** {province_nom}")    # --- AFFICHAGE DE LA RÉPLIQUE ---
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
    row = df[df["barrage_key"] == choice_key.lower()].iloc[0]
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
            st.image(row["image_url"], width="stretch")
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
        
        # --- INITIALISATION ---
        ndwi, ndvi, ndti = None, None, None
        
        with st.spinner("Calcul GEE en cours..."):
            # 1. Calcul des indices
            metrics = get_metrics(lat, lon, start_str, end_str, cloud_pct, radius=5000)
            st.write("--- DEBUG SYSTEM ---")
            st.write(f"Metrics brut : {metrics}")
            st.write(f"Type de metrics : {type(metrics)}")
            # Extraction sécurisée des résultats
            if metrics and isinstance(metrics, dict):
                # Ajoute cette ligne temporaire pour debugger :
                # st.write("Clés reçues :", metrics.keys()) 
                
                ndwi = metrics.get('ndwi') or metrics.get('nd')
                ndvi = metrics.get('ndvi') or metrics.get('nd_1')
                ndti = metrics.get('ndti') or metrics.get('nd_2')
            
            # 2. Calcul de la surface (UNE SEULE FOIS avec le radius)
            # Supprime la deuxième ligne "water =" qui n'avait pas le radius
            water = water_surface(lat, lon, start_str, end_str, cloud_pct, radius=current_radius)

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
            st.plotly_chart(fig, width="stretch")
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

       # --- SECTION RAPPORT PDF (Bien alignée sous tab2) ---
        st.markdown("---")
        if st.button("🏗️ Préparer le rapport PDF"):
            with st.spinner("Génération..."):
                try:
                    pdf_output = generate_pdf(choice, row, ndwi, ndvi, water, rl, rs, al, start_str, end_str, ndti, fig=fig)
                    
                    if hasattr(pdf_output, 'output'):
                        pdf_bytes = pdf_output.output(dest='S').encode('latin-1')
                    elif isinstance(pdf_output, (bytearray, str)):
                        pdf_bytes = bytes(pdf_output) if isinstance(pdf_output, bytearray) else pdf_output.encode('latin-1')
                    else:
                        pdf_bytes = pdf_output
                    
                    st.session_state['pdf_ready'] = pdf_bytes
                except Exception as e:
                    st.error(f"Erreur lors de la génération : {e}")
                    st.session_state['pdf_ready'] = None

        if st.session_state.get('pdf_ready'):
            st.download_button(
                label="📥 Télécharger le Rapport PDF",
                data=st.session_state['pdf_ready'],
                file_name=f"Rapport_{choice}.pdf",
                mime="application/pdf"
            )
        else:
            st.warning("⚠️ Le rapport PDF n'est pas encore prêt.")