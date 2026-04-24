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
@st.cache_data
def load_barrages():
    try:
        # 1. Lecture du CSV
        df_csv = pd.read_csv("Data/barrages.csv")
        
        # Nettoyage des noms de colonnes (on utilise une liste en compréhension, c'est plus sûr)
        df_csv.columns = [str(c).strip().lower() for c in df_csv.columns]
        
        # --- LA CORRECTION EST ICI (.str.lower()) ---
        if 'barrage' in df_csv.columns:
            df_csv['barrage_key'] = df_csv['barrage'].astype(str).str.strip().str.lower().str.replace(' ', '').str.replace('-', '')
        
        # 2. Lecture du GeoJSON
        gdf_sig = gpd.read_file("Data/barrages.geojson")
        gdf_sig.columns = [str(c).strip().lower() for c in gdf_sig.columns]
        
        col_name = 'barrage' if 'barrage' in gdf_sig.columns else gdf_sig.columns[0]
        
        # --- ET ICI AUSSI ---
        gdf_sig['barrage_key'] = gdf_sig[col_name].astype(str).str.strip().str.lower().str.replace(' ', '').str.replace('-', '')
        
        # 3. Fusion
        return gdf_sig.merge(df_csv, on="barrage_key", how="left")
        
    except Exception as e:
        st.error(f"Erreur lors du chargement des données : {e}")
        return pd.DataFrame()
df = load_barrages()

expert_facts = {
    "ALWAHDA": "Deuxième plus grand barrage d'Afrique, pilier de la régulation du Sebou.",
    "OUEDELMAKHAZINE": "Infrastructure stratégique pour la sécurité alimentaire du Gharb.",
    "DARKHROUFA": "Ouvrage de nouvelle génération pour le développement agricole du Loukkos."
}

# ── Sidebar ──
with st.sidebar:
    st.markdown("<div style='text-align:center; font-size:2.5rem;'>💧</div>", unsafe_allow_html=True)
    if not df.empty:
        # On utilise le nom propre pour l'affichage
        barrage_display = sorted(df["barrage_x"].str.upper().unique().tolist())
        choice_name = st.selectbox("🏞 Sélection du barrage :", barrage_display)
        
        row = df[df["barrage_x"].str.upper() == choice_name].iloc[0]
        choice_key = row["barrage_key"].upper()
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
    
    # MODIF : Bounding Box au lieu du Cercle
    delta = 0.08 if choice_key == "ALWAHDA" else 0.05
    bbox = [[lat - delta, lon - delta], [lat + delta, lon + delta]]

    # 1. Header
    st.markdown(f"""
    <div style='display:flex; justify-content:space-between; align-items:flex-end;'>
        <div>
            <div class='dash-title'>سد {row.get('barrage_x', choice_name)}</div>
            <div style='color:#1a4a7c; font-size:1.2rem; font-weight:600;'>Barrage {choice_name.title()}</div>
        </div>
        <div style='color:#6b7fa3; font-size:0.8rem; text-align:right;'>
            {lat:.4f}°N | {lon:.4f}°E | Zone BBox Active
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Correction affichage Province
    st.info(f"**📍 Bassin :** {row.get('bassin','Inconnu')} | **Province :** {row.get('nom_provin', row.get('province','—'))}")

    # 2. Note d'Expert
    fact = expert_facts.get(choice_key, "Infrastructure stratégique nationale.")
    st.markdown(f"""
    <div class="expert-note">
        <span style="color:#148337; font-weight:bold;">💡 ANALYSE STRATÉGIQUE</span><br>{fact}<br>
        <small style="color:#6b7fa3;">Mis en service : {row.get('annee','—')} | Capacité : {row.get('capacite','—')} Mm³</small>
    </div>
    """, unsafe_allow_html=True)

    # 3. Détails & Image
    c1, c2 = st.columns([1.5, 1])
    with c1:
        if "image_url" in row and pd.notna(row["image_url"]):
            st.image(row["image_url"], width='stretch')
        else: st.info("📸 Image satellite non disponible")
    with c2:
        st.subheader("🔍 Fiche Technique")
        st.markdown(f"""
        **📍 Région :** {row.get('nom_region', '—')}  
        **🏢 Province :** {row.get('nom_provin', '—')}  
        **🌊 Bassin :** {row.get('bassin', '—')}  
        **📏 Capacité :** {row.get('capacite', '—')} Mm³  
        **💡 Usages :** {row.get('usage', '—')}
        """)

    # ── Tabs ──
    tab1, tab2, tab3, tab4 = st.tabs(["🗺 CARTE", "📊 ANALYSES SPECTRALES", "⚠️ RISQUES", "📄 RAPPORT"])

    from processing.indices import get_metrics, water_surface, get_timeseries, get_water_surface_area, get_climate_data

    with tab2:
        with st.spinner("Analyse GEE haute performance..."):
            metrics = get_metrics(lat, lon, start_str, end_str, cloud_pct, radius=10000)
            w_surf = water_surface(lat, lon, start_str, end_str, cloud_pct, radius=10000)
            
            val_ndwi = metrics.get('ndwi', 0) if metrics else 0
            val_ndti = metrics.get('ndti', 0) if metrics else 0
            val_ndvi = metrics.get('ndvi', 0) if metrics else 0

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("💧 NDWI", f"{val_ndwi:.3f}")
            m2.metric("🌫️ Turbidité", f"{val_ndti:.3f}")
            m3.metric("🌿 NDVI", f"{val_ndvi:.3f}")
            m4.metric("📐 Surface", f"{w_surf:.2f} km²")

            ts = get_timeseries(lat, lon, start_str, end_str, cloud_pct, radius=10000)
            if ts is not None and not ts.empty:
                fig = px.area(ts, x="date", y="NDWI", title="Historique Remplissage", color_discrete_sequence=['#00c9ff'])
                st.plotly_chart(fig, width='stretch')

    with tab1:
        from streamlit_folium import st_folium
        # Note: Dans build_map, assurez-vous de gérer le paramètre bbox au lieu de radius si vous l'avez modifié
        m = build_map(lat, lon, row, start_str, end_str, cloud_pct, show_ndwi, show_ndvi, show_rgb, show_ndti, radius=10000)
        st_folium(m, width=1200, height=500)

    with tab3:
        from processing.analysis import compute_risk, generate_alerts
        rl, rs = compute_risk(val_ndwi, val_ndvi, val_ndti)
        st.subheader(f"État du réservoir : {rl}")
        st.progress(rs / 100)
        
        flood_risk = (val_ndwi + 0.1) * 100
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