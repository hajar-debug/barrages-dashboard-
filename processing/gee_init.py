import ee
import streamlit as st

def init_gee():
    """Initialise GEE avec les secrets configurés."""
    try:
        if not ee.data_is_initialized():
            # On vérifie si la clé exacte existe dans les secrets
            if "GEE_SERVICE_ACCOUNT" in st.secrets:
                creds = dict(st.secrets["GEE_SERVICE_ACCOUNT"])
                auth = ee.ServiceAccountCredentials(
                    creds['client_email'], 
                    key_data=creds['private_key']
                )
                ee.Initialize(auth, project=creds['project_id'])
            else:
                # Mode local pour ton PC
                ee.Initialize(project='ton-projet-id-local')
    except Exception as e:
        st.error(f"Erreur d'initialisation GEE : {e}")
        raise e