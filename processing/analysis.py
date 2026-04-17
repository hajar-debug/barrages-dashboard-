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


def generate_alerts(ndwi, ndvi, water, ndti=None):
    """Retourne une liste de messages d'alerte incluant la turbidité."""
    alerts = []

    # Alertes Eau (NDWI)
    if ndwi is not None:
        if ndwi < 0.05:
            alerts.append("💧 NDWI critique (< 0.05) — Risque d'assèchement sévère.")
        elif ndwi < 0.10:
            alerts.append("💧 NDWI bas — Le niveau de la retenue est inférieur à la normale.")

    # Alertes Turbidité (NDTI) - AJOUTÉ
    if ndti is not None:
        if ndti > 0.10:
            alerts.append("🌫️ Turbidité élevée — Fort risque d'envasement de la retenue.")
        elif ndti > 0.05:
            alerts.append("🌫️ Eau trouble — Sédiments en suspension détectés.")

    # Alertes Végétation (NDVI)
    if ndvi is not None:
        if ndvi < 0.1:
            alerts.append("🌿 NDVI très bas — Stress hydrique extrême du bassin versant.")

    # Alertes Surface (Water)
    if water is not None:
        if water < 1.0:
            alerts.append(f"📐 Surface réduite ({water:.2f} km²) — Seuil de sécurité atteint.")

    # Alertes Combinées (Aide à la décision)
    if ndwi is not None and ndti is not None:
        if ndwi < 0.1 and ndti > 0.05:
            alerts.append("⚠️ Alerte combinée : Niveau bas + Turbidité — Risque majeur pour les vannes de fond.")

    return alerts