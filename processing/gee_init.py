import ee
import streamlit as st

def init_gee():
    try:
        # On tente d'initialiser. Si ça échoue, on passe à l'authentification par secrets.
        if "GEE_SERVICE_ACCOUNT" in st.secrets:
            creds = st.secrets["GEE_SERVICE_ACCOUNT"]
            
            # Utilisation de la méthode officielle Service Account
            auth = ee.ServiceAccountCredentials(
                creds['client_email'], 
                key_data=creds['private_key']
            )
            
            # On initialise avec les credentials et le projet
            ee.Initialize(auth, project=creds.get('project_id', 'barrages-project'))
        else:
            # Mode local pour ton PC
            ee.Initialize(project='barrages-project')
            
    except Exception as e:
        # Si on arrive ici, c'est que l'initialisation a échoué
        # On vérifie si c'est parce que c'est déjà fait
        try:
            ee.Initialize() 
        except:
            st.error(f"Erreur d'authentification GEE : {e}")
            st.info("Vérifiez vos secrets Streamlit (GEE_SERVICE_ACCOUNT)")
            st.stop()