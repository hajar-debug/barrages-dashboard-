import streamlit as st
import pandas as pd
import plotly.express as px
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

# ── CSS Pro (Gardé tel quel) ──────────────────────────────
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

[data-testid="stSidebar"] .stCheckbox label p {
    color: white !important;
    font-weight: 500 !important;
    font-size: 0.9rem !important;
}

.dash-title {
    font-family: 'Syne', sans-serif;
    font-size: 2.2rem;
    font-weight: 800;
    background: linear-gradient(90deg, #00c9ff, #0066ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0;
}

.dash-sub {
    font-size: 0.9rem;
    color: var(--muted);
    font-weight: 400;
    margin-top: 2px;
}

.section-title {
    font-family: 'Syne', sans-serif;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--accent);
    margin: 20px 0 10px 0;
    border-bottom: 1px solid rgba(30,58,95,0.4);
    padding-bottom: 5px;
}

[data-testid="metric-container"] {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 15px;
}
</style>
""", unsafe_allow_html=True)

# ── Init GEE ──
try:
    init_gee()
except Exception as e:
    st.error(f"Erreur d'initialisation Google Earth Engine : {e}")

# ── Load Data ──
@st.cache_data
def load_barrages():
    try:
        df = pd.read_csv("Data/barrages.csv", encoding='utf-8')
        df.columns = df.columns.str.strip().str.lower()
        return df
    except Exception as e:
        st.error(f"Erreur chargement CSV : {e}")
        return pd.DataFrame()

df = load_barrages()

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

        st.markdown('<div class="section-title">📅 Période</div>', unsafe_allow_html=True)
        start_date = st.date_input("Début", value=pd.to_datetime("2024-01-01"))
        end_date = st.date_input("Fin", value=pd.to_datetime("2026-04-17"))

        st.markdown('<div class="section-title">☁️ Filtre nuages</div>', unsafe_allow_html=True)
        cloud_pct = st.slider("% nuages max", 0, 50, 20)

        st.markdown('<div class="section-title">🗺 Couches carte</div>', unsafe_allow_html=True)
        show_ndwi  = st.checkbox("💧 NDWI (Eau)", value=True)
        show_ndti  = st.checkbox("🌫️ NDTI (Turbidité)", value=True)
        show_ndvi  = st.checkbox("🌿 NDVI (Végétation)", value=True)
        show_rgb   = st.checkbox("📷 Satellite RGB", value=False)

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
        <div style='color:var(--muted); font-size:0.8rem;'>{lat:.4f}°N | {lon:.4f}°E</div>
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
    tab1, tab2, tab3, tab4 = st.tabs(["🗺 CARTE", "📊 ANALYSES", "⚠️ RISQUES", "📄 RAPPORT"])

    with tab1:
        from streamlit_folium import st_folium
        m = build_map(
            lat, lon, row, start_str, end_str, 
            cloud_pct, show_ndwi, show_ndvi, show_rgb, show_ndti
        )
        st_folium(m, width='stretch') 


    with tab2:
        from processing.indices import get_metrics, water_surface, get_timeseries
        import plotly.express as px
        
        with st.spinner("Calcul GEE en cours..."):
            metrics = get_metrics(lat, lon, start_str, end_str, cloud_pct)
            ndwi, ndvi, ndti = metrics['ndwi'], metrics['ndvi'], metrics['ndti']
            water = water_surface(lat, lon, start_str, end_str, cloud_pct)

        # Les métriques s'affichent d'abord
        c1, c2, c3, c4 = st.columns(4) 
        c1.metric("💧 NDWI", f"{ndwi:.3f}" if ndwi else "N/A")
        c2.metric("🌫️ NDTI", f"{ndti:.3f}" if ndti else "N/A") 
        c3.metric("🌿 NDVI", f"{ndvi:.3f}" if ndvi else "N/A")
        c4.metric("📐 Surface", f"{water:.2f} km²" if water else "N/A")

        st.markdown("### 📈 Évolution Temporelle")

        # --- BLOC GRAPHIQUE (Réaligné strictement sous tab2) ---
        ts = get_timeseries(lat, lon, start_str, end_str, cloud_pct)
        fig = None 
        
        if ts is not None and not ts.empty:
            fig = px.line(
                ts, 
                x="date", 
                y=["NDWI", "Turbidité"], 
                template="plotly_dark",
                color_discrete_map={"NDWI": "#00c9ff", "Turbidité": "#ffa500"}
            )
            fig.update_layout(
                xaxis_title="Date d'acquisition",
                yaxis_title="Valeur de l'indice",
                hovermode="x unified"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("📊 Aucune donnée historique disponible pour cette période.")

        st.markdown("### 🛰️ Bilan de Surface (Analyse Comparative)")
    col_a, col_b = st.columns(2)
    
        with col_a:
        surface_initiale = get_water_surface_area(lat, lon, "2024-01-01", cloud_pct)
        st.metric("Surface Janvier 2024", f"{surface_initiale:.2f} km²")
        
        with col_b:
        surface_actuelle = get_water_surface_area(lat, lon, end_str, cloud_pct)
        delta = surface_actuelle - surface_initiale
        st.metric("Surface Actuelle", f"{surface_actuelle:.2f} km²", delta=f"{delta:.2f} km²")

        if surface_actuelle < surface_initiale:
        st.warning(f"⚠️ Perte de surface liquide de {abs(delta):.2f} km² par rapport à 2024.")
        with st.expander("🔬 Méthodologie et Interprétation des Indices"):
            st.write("""
        ### 1. NDWI (Normalized Difference Water Index)
        **Formule :** $(Green - NIR) / (Green + NIR)$  
        * **Utilité :** Maximise la réflectance de l'eau.
        * **Interprétation :** Valeurs > 0.2 indiquent de l'eau libre.

        ### 2. NDTI (Normalized Difference Turbidity Index)
        **Formule :** $(Red - Green) / (Red + Green)$  
        * **Utilité :** Mesure la concentration de sédiments.

        ### 3. NDVI (Normalized Difference Vegetation Index)
        **Formule :** $(NIR - Red) / (NIR + Red)$  
        """)

    # AJOUT DU TABLEAU DE TEMPÉRATURE
        from processing.indices import get_climate_data
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
        
        if ndti and ndti > 0.1:
            st.error("🚨 Alerte : Turbidité élevée détectée (Risque d'envasement)")
            
        for a in al: st.warning(a)
# Dans l'onglet ANALYSES (tab2)
    with tab2:
        # ... (Garde ton code actuel pour les métriques et le graphique) ...
        
        # AJOUT DU TABLEAU DE TEMPÉRATURE
        from processing.indices import get_climate_data
        st.markdown("### 🌡️ Contexte Climatique")
        temp_actuelle = get_climate_data(lat, lon, end_str)
        
        climat_df = pd.DataFrame({
            "Indicateur": ["Température Moyenne", "Évapotranspiration (est.)", "État du Ciel"],
            "Valeur": [f"{temp_actuelle:.1f} °C", "4.5 mm/jour", "Dégagé" if cloud_pct < 20 else "Nuageux"],
            "Impact": ["Normal", "Risque de perte d'eau", "Optimale"]
        })
        st.table(climat_df)

    # Dans l'onglet RISQUES (tab3)
    with tab3:
        st.subheader("🌊 Alerte Prédictive Inondation")
        
        # Logique de prédiction simplifiée (Valeur ajoutée Master)
        # On croise le remplissage actuel (NDWI) avec un facteur de risque
        flood_risk = (ndwi + 0.1) * 100 if ndwi else 0
        
        if flood_risk > 80:
            st.error(f"🚨 RISQUE CRITIQUE ({flood_risk:.1f}%) : Capacité maximale atteinte.")
        elif flood_risk > 50:
            st.warning(f"⚠️ VIGILANCE ({flood_risk:.1f}%) : Niveau élevé, surveillance accrue.")
        else:
            st.success(f"✅ RISQUE FAIBLE ({flood_risk:.1f}%) : Capacité de stockage disponible.")

    # Tableau de Température & Climat
    st.markdown("### 🌡️ Paramètres Météorologiques")
    t_col1, t_col2 = st.columns(2)
    
    # On peut imaginer un petit DataFrame pour le tableau
    climat_data = {
        "Paramètre": ["Température Moyenne", "Évapotranspiration", "Humidité du sol"],
        "Valeur": [f"{temp_c:.1f} °C", "4.2 mm/j", "0.28 m³/m³"],
        "Statut": ["Normal", "Élevé", "Saturé"]
    }
    st.table(climat_data)
    with tab4:
        st.markdown("### 📄 Analyse Hydrologique & Rapport")
        
        # 1. Logique d'interprétation dynamique
        interpretation = ""
        
        if ndwi is not None:
            # Pour un grand barrage, un NDWI moyen > 0.15 indique souvent un remplissage massif
            if ndwi > 0.15: 
                st.success("🌊 **DIAGNOSTIC : CRUE / REMPLISSAGE ÉLEVÉ**")
                interpretation += "✅ **État de l'eau** : La retenue affiche un indice de présence d'eau élevé, typique des périodes de fortes précipitations.\n\n"
            elif ndwi > 0.02:
                st.info("📊 **DIAGNOSTIC : NIVEAU NORMAL**")
                interpretation += "⚠️ **État de l'eau** : Niveau de remplissage moyen.\n\n"
            else:
                st.error("🚨 **DIAGNOSTIC : ALERTE SÉCHERESSE**")
                interpretation += "🚨 **Alerte** : Très faible réflectance de l'eau. Risque de déficit hydrique sévère.\n\n"
        
        if ndti is not None:
            if ndti > 0.05:
                st.warning("🌫️ **TURBIDITÉ ÉLEVÉE**")
                interpretation += "🌫️ **Qualité** : Forte concentration de sédiments détectée, suggérant un apport de boues par les oueds (crues) ou un envasement important.\n\n"
            else:
                interpretation += "✨ **Qualité** : Eau claire avec peu de sédiments en suspension.\n\n"

        if st.button("🏗️ Préparer le rapport PDF"):
            with st.spinner("Rédaction du rapport avec graphiques..."):
                # AJOUT : Passage du paramètre fig=fig
                pdf_output = generate_pdf(choice, row, ndwi, ndvi, water, rl, rs, al, start_str, end_str, ndti, fig=fig)
                
                # Conversion sécurisée en bytes
                if isinstance(pdf_output, str):
                    pdf_bytes = pdf_output.encode('latin-1')
                else:
                    pdf_bytes = bytes(pdf_output)

                st.success("✅ Rapport prêt !")
                st.download_button(
                    label="📥 Télécharger le rapport (PDF)",
                    data=pdf_bytes,
                    file_name=f"Rapport_{choice}_{datetime.now().strftime('%d-%m-%y')}.pdf",
                    mime="application/pdf"
                )

        st.markdown("---")
        st.subheader("💡 Interprétation Experte")
        st.info(interpretation if interpretation else "Sélectionnez une période.")

    
st.markdown("### 🏥 Bilan de Santé du Réservoir")
col1, col2, col3 = st.columns(3)

with col1:
    # État du remplissage (Basé sur le NDWI)
    st.write("**💧 Remplissage**")
    if ndwi > 0.2:
        st.success("Excellent")
    elif ndwi > 0.05:
        st.warning("Moyen")
    else:
        st.error("Critique")

with col2:
    # État de la qualité / Sédiments (Basé sur le NDTI)
    st.write("**🌫️ Qualité de l'eau**")
    if ndti < 0.02:
        st.success("Claire")
    elif ndti < 0.1:
        st.warning("Chargée")
    else:
        st.error("Trés Turbide")

with col3:
    # État des berges (Basé sur le NDVI)
    st.write("**🌿 Protection Berges**")
    if ndvi > 0.3:
        st.success("Stable")
    else:
        st.warning("Risque d'Érosion")
