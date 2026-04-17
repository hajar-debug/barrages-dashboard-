import ee
import streamlit as st

def init_gee():
    try:
        # On essaie d'abord de voir si GEE est déjà prêt
        ee.Initialize()
    except:
        # Si non, on utilise les secrets
        if "GEE_SERVICE_ACCOUNT" in st.secrets:
            creds = dict(st.secrets["GEE_SERVICE_ACCOUNT"])
            auth = ee.ServiceAccountCredentials(
                creds['client_email'], 
                key_data=creds['private_key']
            )
            ee.Initialize(auth, project=creds.get('project_id'))
        else:
            # Mode local pour tes tests
            ee.Initialize(project='barrages-project')