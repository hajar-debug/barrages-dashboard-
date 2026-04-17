import ee
import streamlit as st

def init_gee():
    try:
        # Test si déjà initialisé
        ee.Initialize()
    except:
        # Si non, on cherche les secrets
        if "GEE_SERVICE_ACCOUNT" in st.secrets:
            creds = dict(st.secrets["GEE_SERVICE_ACCOUNT"])
            auth = ee.ServiceAccountCredentials(
                creds['client_email'], 
                key_data=creds['private_key']
            )
            ee.Initialize(auth, project=creds.get('project_id'))
        else:
            # Mode local pour ton PC
            ee.Initialize(project='barrages-project')