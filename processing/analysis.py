def compute_risk(ndwi, ndvi):
    """
    Calcule un score de risque 0-100 et un niveau textuel.
    
    Logique :
    - NDWI faible  → risque eau élevé
    - NDVI faible  → stress végétatif / sécheresse bassin versant
    """
    score = 50  # valeur neutre par défaut

    if ndwi is not None:
        if ndwi < 0.05:
            score += 30
        elif ndwi < 0.15:
            score += 15
        else:
            score -= 15

    if ndvi is not None:
        if ndvi < 0.1:
            score += 20
        elif ndvi < 0.3:
            score += 5
        else:
            score -= 10

    score = max(0, min(100, score))

    if score >= 65:
        level = "🔴 Critique"
    elif score >= 40:
        level = "🟠 Moyen"
    else:
        level = "🟢 Faible"

    return level, score


def generate_alerts(ndwi, ndvi, water):
    """Retourne une liste de messages d'alerte selon les indices."""
    alerts = []

    if ndwi is not None:
        if ndwi < 0.05:
            alerts.append("NDWI très bas (< 0.05) — Risque d'envasement ou niveau d'eau critique.")
        elif ndwi < 0.10:
            alerts.append("NDWI bas (< 0.10) — Surveillance recommandée du niveau du lac.")

    if ndvi is not None:
        if ndvi < 0.1:
            alerts.append("NDVI très bas (< 0.10) — Stress hydrique sévère dans le bassin versant.")
        elif ndvi < 0.2:
            alerts.append("NDVI faible (< 0.20) — Dégradation végétale détectée.")

    if water is not None:
        if water < 1.0:
            alerts.append(f"Surface d'eau estimée à {water:.2f} km² — Niveau très bas.")
        elif water < 5.0:
            alerts.append(f"Surface d'eau ({water:.2f} km²) en dessous du seuil normal.")

    if ndwi is not None and ndvi is not None and ndwi < 0.1 and ndvi < 0.2:
        alerts.append("⚠️ Combinaison NDWI + NDVI faibles — Risque de sécheresse généralisée.")

    return alerts
 