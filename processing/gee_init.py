import ee

def init_gee():
    try:
        # REMPLACEZ 'votre-projet-id' par l'ID réel trouvé à l'étape 1
        ee.Initialize(project='barrages-project')
        print("✅ GEE initialisé avec succès !")
    except Exception as e:
        # Si vous n'avez pas de projet fixe, cette ligne tente de récupérer le projet par défaut
        try:
            ee.Initialize() 
        except:
            print(f"❌ Erreur d'initialisation GEE : {e}")
            raise e