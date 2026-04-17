def compute_risk(ndwi, ndvi, ndti=None):
    """
    Calcule un score de risque 0-100 en intégrant la turbidité.
    Logique :
    - NDWI faible  → Risque sécheresse
    - NDVI faible  → Stress bassin versant
    - NDTI élevé   → Risque envasement (nouveau)
    """
    score = 50  # valeur neutre

    # 1. Analyse NDWI (Disponibilité en eau)
    if ndwi is not None:
        if ndwi < 0.05:
            score += 25
        elif ndwi < 0.15:
            score += 10
        else:
            score -= 15

    # 2. Analyse NDVI (Couverture végétale)
    if ndvi is not None:
        if ndvi < 0.1:
            score += 15
        elif ndvi < 0.3:
            score += 5
        else:
            score -= 10

    # 3. Analyse NDTI (Turbidité / Envasement) - AJOUTÉ
    if ndti is not None:
        if ndti > 0.15:    # Eau très chargée
            score += 20
        elif ndti > 0.05:  # Eau modérément chargée
            score += 10

    score = max(0, min(100, score))

    if score >= 70:
        level = "🔴 Critique"
    elif score >= 45:
        level = "🟠 Moyen"
    else:
        level = "🟢 Faible"

    return level, score


# Dans processing/analysis.py

def generate_alerts(ndwi, ndvi, water, ndti=None):
    alerts = []
    
    # Alertes de Stress Hydrique (Sécheresse)
    if ndwi is not None:
        if ndwi < 0.05:
            alerts.append("🔴 **Alerte Sécheresse Critique** : Le retrait de la nappe d'eau est majeur. Risque d'arrêt des prises d'eau potable.")
        elif ndwi < 0.15:
            alerts.append("🟠 **Vigilance Hydrique** : Baisse significative du niveau de remplissage observée.")

    # Alertes d'Envasement (Sédimentologie)
    if ndti is not None:
        if ndti > 0.15:
            alerts.append("🔴 **Alerte Sédimentation** : Forte turbidité détectée. Risque d'envasement des vannes de fond et dégradation de la qualité de l'eau.")
        elif ndti > 0.05:
            alerts.append("🟡 **Avis de Turbidité** : Augmentation des matières en suspension. Possible apport solide suite à des précipitations.")

    # Alertes du Bassin Versant (Érosion/Eutrophisation)
    if ndvi is not None:
        if ndvi < 0.15:
            alerts.append("⚠️ **Dégradation Couverture Végétale** : Risque accru d'érosion des sols vers la retenue lors des prochaines pluies.")
        elif ndvi > 0.6:
            alerts.append("🌿 **Risque d'Eutrophisation** : Prolifération végétale détectée pouvant réduire l'oxygène dissous dans l'eau.")

    # Alertes Combinées (Aide à la décision)
    if ndwi is not None and ndti is not None:
        if ndwi < 0.1 and ndti > 0.05:
            alerts.append("⚠️ Alerte combinée : Niveau bas + Turbidité — Risque majeur pour les vannes de fond.")

    return alerts