import ee
import streamlit as st

def init_gee():
    """Initialisation sécurisée pour Streamlit Cloud."""
    try:
        # 1. On vérifie si GEE est déjà initialisé
        try:
    ee.Initialize()
except:
    # Si non initialisé, on continue vers l'authentification
    pass
            # 2. On cherche tes secrets que tu viens de coller
            if "GEE_SERVICE_ACCOUNT" in st.secrets:
                creds = dict(st.secrets["GEE_SERVICE_ACCOUNT"])
                
                # Authentification avec la clé privée
                auth = ee.ServiceAccountCredentials(
                    creds['client_email'], 
                    key_data=creds['private_key']
                )
                ee.Initialize(auth, project=creds['project_id'])
                print("✅ GEE connecté avec succès sur le Cloud")
            else:
                # Mode local pour tes tests sur PC
                ee.Initialize(project='barrages-project')
                print("✅ GEE connecté en local")
                
    except Exception as e:
        # Si une erreur survient, on l'affiche proprement
        if "already initialized" not in str(e).lower():
            st.error(f"Erreur d'authentification GEE : {e}")