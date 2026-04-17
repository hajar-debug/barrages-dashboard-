import ee
import streamlit as st

def init_gee():
    """Initialise Google Earth Engine en utilisant les Service Account Secrets."""
    try:
        # 1. On vérifie si GEE est déjà initialisé pour éviter de le refaire
        ee.Initialize()
    except Exception:
        try:
            # 2. Tentative d'initialisation via les Secrets Streamlit Cloud
            if "GEE_SERVICE_ACCOUNT" in st.secrets:
                creds = st.secrets["GEE_SERVICE_ACCOUNT"]
                
                # On crée les identifiants à partir du Service Account
                auth = ee.ServiceAccountCredentials(
                    creds['client_email'], 
                    key_data=creds['private_key']
                )
                
                # Initialisation officielle avec le projet spécifié
                ee.Initialize(auth, project=creds.get('project_id', 'barrages-project'))
            else:
                # 3. Fallback pour ton PC local (si tu as gcloud installé)
                ee.Initialize(project='barrages-project')
        except Exception as e:
            st.error(f"Erreur fatale lors de l'initialisation de Google Earth Engine : {e}")
            st.info("Vérifiez que vos secrets 'client_email' et 'private_key' sont corrects dans Streamlit Cloud.")