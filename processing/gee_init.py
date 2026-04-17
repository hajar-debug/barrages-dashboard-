import ee
import streamlit as st

def init_gee():
    """Initialise GEE sans utiliser d'attributs obsolètes."""
    try:
        # On essaie de voir si une clé existe, peu importe son nom
        creds_dict = None
        if "GEE_SERVICE_ACCOUNT" in st.secrets:
            creds_dict = dict(st.secrets["GEE_SERVICE_ACCOUNT"])
        elif "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])

        if creds_dict:
            # MODE CLOUD
            auth = ee.ServiceAccountCredentials(
                creds_dict['client_email'], 
                key_data=creds_dict['private_key']
            )
            ee.Initialize(auth, project=creds_dict.get('project_id'))
        else:
            # MODE LOCAL
            ee.Initialize(project='barrages-project')
            
    except Exception as e:
        # Si c'est déjà initialisé, on ne fait rien, sinon on affiche l'erreur
        if "already initialized" not in str(e).lower():
            st.error(f"Erreur d'initialisation GEE : {e}")
            raise e