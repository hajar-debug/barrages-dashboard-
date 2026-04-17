import ee
import streamlit as st

def init_gee():
    try:
        # On vérifie si déjà initialisé
        if ee.data._credentials is not None:
            return
            
        # FORCE l'utilisation des secrets
        if "GEE_SERVICE_ACCOUNT" in st.secrets:
            creds = st.secrets["GEE_SERVICE_ACCOUNT"]
            auth = ee.ServiceAccountCredentials(
                creds['client_email'], 
                key_data=creds['private_key']
            )
            ee.Initialize(auth, project=creds.get('project_id', 'barrages-project'))
            st.success("✅ Connexion Google Earth Engine établie avec succès !")
        else:
            # Uniquement pour ton test local sur PC
            ee.Initialize(project='barrages-project')
    except Exception as e:
        st.error(f"Erreur GEE : {e}")
        st.info("Vérifiez vos secrets Streamlit (GEE_SERVICE_ACCOUNT)")
        st.stop()