import streamlit as st
import pandas as pd
from processing.gee_init import init_gee

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

    # Dans app.py, onglet tab1 (CARTE)
    with tab1:
        from processing.maps import build_map
        from streamlit_folium import st_folium
    
    # Vérifie bien que show_ndti est ajouté à la fin ici :
    m = build_map(
        lat, lon, row, start_str, end_str, 
        cloud_pct, show_ndwi, show_ndvi, show_rgb, show_ndti
    )
    
    st_folium(m, width="stretch", height=550, returned_objects=[]) 
    with tab2:
        from processing.indices import get_metrics, water_surface, get_timeseries
        with st.spinner("Calcul GEE en cours..."):
            metrics = get_metrics(lat, lon, start_str, end_str, cloud_pct)
            ndwi, ndvi, ndti = metrics['ndwi'], metrics['ndvi'], metrics['ndti']
            water = water_surface(lat, lon, start_str, end_str, cloud_pct)

        c1, c2, c3, c4 = st.columns(4) 
        c1.metric("💧 NDWI", f"{ndwi:.3f}" if ndwi else "N/A")
        c2.metric("🌫️ NDTI", f"{ndti:.3f}" if ndti else "N/A") 
        c3.metric("🌿 NDVI", f"{ndvi:.3f}" if ndvi else "N/A")
        c4.metric("📐 Surface", f"{water:.2f} km²" if water else "N/A")

        ts = get_timeseries(lat, lon, start_str, end_str, cloud_pct)
        if ts is not None and not ts.empty:
            import plotly.express as px
            fig = px.line(ts, x="date", y=["NDWI", "Turbidité"], template="plotly_dark")
            st.plotly_chart(fig, width="stretch")
    st.markdown("---")
    with st.expander("🔬 Méthodologie et Interprétation des Indices"):
        st.write("""
        ### 1. NDWI (Normalized Difference Water Index)
        **Formule :** $(Green - NIR) / (Green + NIR)$  
        * **Utilité :** Maximise la réflectance de l'eau en utilisant la bande verte et minimise la faible réflectance de l'eau dans le proche infrarouge.
        * **Interprétation :** Valeurs > 0.2 indiquent de l'eau libre.

        ### 2. NDTI (Normalized Difference Turbidity Index)
        **Formule :** $(Red - Green) / (Red + Green)$  
        * **Utilité :** Mesure la concentration de sédiments en suspension.
        * **Interprétation :** Des valeurs positives indiquent une eau chargée (trouble), souvent liée à l'envasement.

        ### 3. NDVI (Normalized Difference Vegetation Index)
        **Formule :** $(NIR - Red) / (NIR + Red)$  
        * **Utilité :** Évalue la vigueur de la végétation autour du barrage.
        * **Interprétation :** Un NDVI faible (< 0.2) signifie un sol nu ou un stress hydrique.
        """)

    with tab3:
        from processing.analysis import compute_risk, generate_alerts
        # MODIF 2 : Passage du paramètre ndti pour le calcul du risque et les alertes
        rl, rs = compute_risk(ndwi, ndvi, ndti)
        al = generate_alerts(ndwi, ndvi, water, ndti)
        
        st.subheader(f"État du réservoir : {rl}")
        st.progress(rs / 100)
        
        if ndti and ndti > 0.1:
            st.error("🚨 Alerte : Turbidité élevée détectée (Risque d'envasement)")
            
        for a in al: st.warning(a)

    with tab4:
        st.markdown("### 📄 Génération du Rapport d'Analyse")
        st.write("Ce rapport compile les données techniques et une interprétation experte.")

        from report.report_generator import generate_pdf
        from datetime import datetime

        interpretation = ""
        if ndwi is not None:
            if ndwi > 0.2: interpretation += "✅ **État de l'eau** : Présence d'une nappe d'eau claire.\n\n"
            elif ndwi > 0: interpretation += "⚠️ **État de l'eau** : Eau turbide ou faible profondeur.\n\n"
            else: interpretation += "🚨 **Alerte** : Déficit hydrique sévère.\n\n"
        
        if ndti and ndti > 0.05: 
            interpretation += "🌫️ **Turbidité** : Concentration élevée de sédiments en suspension.\n\n"
    
        if ndvi is not None:
            if ndvi > 0.4: interpretation += "🌿 **Végétation** : Forte densité végétale (risque d'eutrophisation).\n"
            else: interpretation += "🍂 **Végétation** : Couverture végétale normale.\n"

        if st.button("🏗️ Préparer le rapport PDF"):
            with st.spinner("Rédaction du rapport..."):
                # MODIF 3 : Ajout du paramètre ndti pour le PDF
                pdf_output = generate_pdf(choice, row, ndwi, ndvi, water, rl, rs, al, start_str, end_str, ndti)
                
                if isinstance(pdf_output, str):
                    pdf_bytes = pdf_output.encode('latin-1')
                elif isinstance(pdf_output, bytearray):
                    pdf_bytes = bytes(pdf_output)
                else:
                    pdf_bytes = pdf_output

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