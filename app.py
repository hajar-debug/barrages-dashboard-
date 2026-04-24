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
    [data-testid="stAppViewContainer"] { background-color: #ffffff !important; color: #1a1a1a !important; }
    [data-testid="stSidebar"] { background-color: #f8f9fa !important; }
    .dash-title { font-family: 'Inter', sans-serif; font-size: 2.8rem; font-weight: 800; color: #1a4a7c; border-bottom: 3px solid #c1272d; padding-bottom: 10px; }
    .expert-note { background: #fff5f5; border-right: 5px solid #148337; border-left: 5px solid #c1272d; padding: 20px; border-radius: 10px; margin: 20px 0; color: #1a4a7c; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    [data-testid="metric-container"] { background: #ffffff !important; border: 1px solid #e0e0e0 !important; border-radius: 10px !important; box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important; color: #1a4a7c !important; }
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
    try:
        # On charge uniquement le CSV (Plus besoin de GeoJSON)
        df = pd.read_csv("Data/barrages.csv")
        df.columns = df.columns.str.strip().str.lower()
        
        # Nettoyage des noms pour la recherche
        df['barrage_key'] = df['barrage'].astype(str).str.strip().str.lower()
        return df
    except Exception as e:
        st.error(f"Erreur de lecture du fichier CSV : {e}")
        return pd.DataFrame()

df = load_barrages()

expert_facts = {
    "ALWAHDA": "Deuxième plus grand barrage d'Afrique, pilier de la régulation du Sebou.",
    "OUEDELMAKHAZINE": "Infrastructure stratégique pour la sécurité alimentaire du Gharb.",
    "DARKHROUFA": "Ouvrage de nouvelle génération pour le développement agricole du Loukkos.",
    "MOULAYABDELLAH": "Barrage vital pour l'alimentation en eau potable de la région d'Agadir."
}

# ── Sidebar ──
with st.sidebar:
    st.title("💧 Configuration")
    if not df.empty:
        barrage_list = sorted(df["barrage_key"].str.upper().unique().tolist())
        choice_key = st.selectbox("🏞 Sélection du barrage :", barrage_list)
        
        # Récupération sécurisée des données de la ligne
        row = df[df["barrage_key"] == choice_key.lower()].iloc[0]
        
        # Gestion des noms de colonnes lat/lon (flexibilité)
        lat = float(row.get('lat', row.get('latitude', 0)))
        lon = float(row.get('lon', row.get('longitude', 0)))

        st.markdown('---')
        start_date = st.date_input("📅 Début", value=pd.to_datetime("2024-01-01"))
        end_date = st.date_input("📅 Fin", value=datetime.now())
        cloud_pct = st.slider("☁️ Nuages max (%)", 0, 100, 30)
        
        st.markdown('---')
        show_ndwi = st.checkbox("💧 NDWI", value=True)
        show_ndti = st.checkbox("🌫️ NDTI", value=True)
        show_ndvi = st.checkbox("🌿 NDVI", value=False)
        show_rgb  = st.checkbox("📷 Satellite RGB", value=False)

# ── MAIN INTERFACE ──
if not df.empty:
    start_str, end_str = start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
    
   # --- SÉCURITÉ : On définit choice_name au cas où ---
    choice_name = choice_key.title()

    # 1. Header (CORRIGÉ)
    st.markdown(f"""
    <div style='display:flex; justify-content:space-between; align-items:flex-end;'>
        <div>
            <div class='dash-title'>سد {choice_name}</div>
            <div style='color:#1a4a7c; font-size:1.2rem; font-weight:600;'>Barrage {choice_name}</div>
        </div>
        <div style='color:#6b7fa3; font-size:0.8rem; text-align:right;'>
            {lat:.4f}°N | {lon:.4f}°E | Zone BBox Active
        </div>
    </div>
    """, unsafe_allow_html=True)
    # Correction affichage métadonnées
    def get_val(key):
        v = row.get(key, '—')
        return v if pd.notna(v) and v != '' else '—'

    bassin = get_val('bassin')
    province = get_val('nom_provin') if get_val('nom_provin') != '—' else get_val('province')
    
    st.info(f"**📍 Bassin :** {bassin} | **Province :** {province}")

    # 2. Note d'Expert
    fact = expert_facts.get(choice_key, "Infrastructure stratégique nationale.")
    st.markdown(f"""
    <div class="expert-note">
        <span style="color:#148337; font-weight:bold;">💡 ANALYSE STRATÉGIQUE</span><br>{fact}<br>
        <small style="color:#6b7fa3;">Mis en service : {get_val('annee')} | Capacité : {get_val('capacite')} Mm³</small>
    </div>
    """, unsafe_allow_html=True)

    # 3. Détails & Image
    c1, c2 = st.columns([1.5, 1])
    with c1:
        if "image_url" in row and pd.notna(row["image_url"]):
            st.image(row["image_url"],width='stretch')
        else: 
            st.info("📸 Image satellite fixe non disponible")
    with c2:
        st.subheader("🔍 Fiche Technique")
        st.markdown(f"""
        **📍 Région :** {get_val('nom_region')}  
        **🏢 Province :** {province}  
        **🌊 Bassin :** {bassin}  
        **📏 Capacité :** {get_val('capacite')} Mm³  
        **💡 Usages :** {get_val('usage')}
        """)
    # --- ÉTAPE DE CALCUL (Ligne 138) ---
with st.spinner("Analyse GEE haute performance..."):
    # Appuie sur la touche TAB une fois au début de chaque ligne ci-dessous :
    metrics = get_metrics(lat, lon, start_str, end_str, cloud_pct, radius=10000)
    water = water_surface(lat, lon, start_str, end_str, cloud_pct, radius=10000)
    
    # On récupère les valeurs pour les onglets
    ndwi = metrics.get('ndwi', 0) if metrics else 0
    ndti = metrics.get('ndti', 0) if metrics else 0
    ndvi = metrics.get('ndvi', 0) if metrics else 0

# --- FIN DU BLOC (Retour à la marge de gauche) ---
tab1, tab2, tab3, tab4 = st.tabs(["🗺 CARTE", "📊 ANALYSES SPECTRALES", "⚠️ RISQUES", "📄 RAPPORT"])

    with tab1:
        from streamlit_folium import st_folium
        m = build_map(
            lat, lon, row, start_str, end_str,
            cloud_pct, show_ndwi, show_ndvi, show_rgb, show_ndti, radius=current_radius
        )
        st_folium(m, width='stretch')


    with tab2:
        from processing.indices import get_metrics, water_surface, get_timeseries
        with st.spinner("Analyse GEE haute performance..."):
            # On augmente le rayon pour être sûr de couvrir tout le barrage
            calc_radius = current_radius if current_radius > 5000 else 8000
           
            # Appel des fonctions avec un timeout virtuel (via GEE)
            metrics = get_metrics(lat, lon, start_str, end_str, cloud_pct, radius=calc_radius)
            w_surf = water_surface(lat, lon, start_str, end_str, cloud_pct, radius=calc_radius)
           
            # Affichage immédiat
            m1, m2, m3, m4 = st.columns(4)
            val_ndwi = metrics.get('ndwi', 0) if metrics else 0
            val_ndti = metrics.get('ndti', 0) if metrics else 0
            val_ndvi = metrics.get('ndvi', 0) if metrics else 0


            m1.metric("💧 NDWI (Eau)", f"{val_ndwi:.3f}")
            m2.metric("🌫️ Turbidité", f"{val_ndti:.3f}")
            m3.metric("🌿 Végétation", f"{val_ndvi:.3f}")
            m4.metric("📐 Surface", f"{w_surf:.2f} km²")


            # Graphique simplifié pour la vitesse
            ts = get_timeseries(lat, lon, start_str, end_str, cloud_pct, radius=calc_radius)
            if ts is not None and not ts.empty:
                fig = px.area(ts, x="date", y="NDWI", title="Remplissage historique", color_discrete_sequence=['#00c9ff'])
                st.plotly_chart(fig, use_container_width=True)
       
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
