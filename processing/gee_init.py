import ee
import streamlit as st

def init_gee():
    try:
        # Sur Streamlit Cloud → utilise les secrets
        credentials = ee.ServiceAccountCredentials(
            email=st.secrets["GEE_SERVICE_ACCOUNT"],
            key_data=st.secrets["GEE_PRIVATE_KEY"],
        )
        ee.Initialize(credentials)
    except Exception as e:
        st.error(f"❌ Erreur GEE : {e}")
        st.stop()
        