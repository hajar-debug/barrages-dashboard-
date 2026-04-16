from fpdf import FPDF
import io
from datetime import datetime

class BarragePDF(FPDF):
    def header(self):
        # Fond du header
        self.set_fill_color(10, 14, 26)
        self.rect(0, 0, 210, 30, "F")
        
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(0, 201, 255)
        self.set_xy(10, 8)
        self.cell(0, 10, "DASHBOARD BARRAGES MAROC", ln=False)
        
        self.set_font("Helvetica", "", 8)
        self.set_text_color(107, 127, 163)
        self.set_xy(10, 20)
        # Correction : suppression de l'accent sur "généré" pour éviter KeyError
        self.cell(0, 6, f"Rapport genere le {datetime.now().strftime('%d/%m/%Y a %H:%M')}")
        self.ln(18)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(107, 127, 163)
        self.cell(0, 10, f"Page {self.page_no()} | Systeme de Surveillance SIG des Barrages Marocains", align="C")

    def section_title(self, title):
        self.set_fill_color(17, 24, 39)
        self.set_text_color(0, 201, 255)
        self.set_font("Helvetica", "B", 10)
        self.set_x(10)
        self.cell(190, 8, f"  {title}", fill=True, ln=True)
        self.ln(3)

    def info_row(self, label, value, alt=False):
        self.set_font("Helvetica", "", 9)
        self.set_fill_color(26, 34, 53) if alt else self.set_fill_color(17, 24, 39)
        self.set_text_color(107, 127, 163)
        self.set_x(10)
        self.cell(70, 7, label, fill=True)
        self.set_text_color(232, 237, 245)
        # On force value en string et on retire les caractères non-latin1 si besoin
        val_clean = str(value).encode('latin-1', 'replace').decode('latin-1')
        self.cell(120, 7, val_clean, fill=True, ln=True)

    def metric_box(self, label, value, color_rgb=(0, 201, 255)):
        x, y = self.get_x(), self.get_y()
        self.set_fill_color(26, 34, 53)
        self.rect(x, y, 58, 22, "F")
        self.set_font("Helvetica", "", 8)
        self.set_text_color(107, 127, 163)
        self.set_xy(x + 3, y + 3)
        self.cell(52, 5, label)
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(*color_rgb)
        self.set_xy(x + 3, y + 10)
        self.cell(52, 10, str(value))

def generate_pdf(barrage_name, row, ndwi, ndvi, water,
                  risk_level, risk_score, alerts, start, end):
    
    pdf = BarragePDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # ── Titre barrage ──────────────────────────────────────────────────────
    pdf.set_fill_color(0, 102, 255)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_x(10)
    pdf.cell(190, 12, f"  Barrage : {barrage_name}", fill=True, ln=True)
    pdf.ln(4)

    # ── Période (Correction : flèche remplacée par 'au') ────────────────────
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(107, 127, 163)
    pdf.set_x(10)
    pdf.cell(190, 6, f"Periode d'analyse : {start} au {end}", ln=True)
    pdf.ln(4)

    # ── Fiche technique ────────────────────────────────────────────────────
    pdf.section_title("FICHE TECHNIQUE")
    # Note: On utilise row.get(nom_colonne) en minuscules car on a nettoyé le DF avant
    fields = [
        ("Nom officiel",     row.get("barrage", "—")),
        ("Capacite (Mm3)",   row.get("capacite", "—")),
        ("Region",           row.get("nom_region", "—")),
        ("Province",         row.get("nom_provin", "—")),
        ("Commune",          row.get("nom_commun", "—")),
        ("Coordonnees",      f"{row.get('lat','—')} N, {row.get('lon','—')} E"),
    ]
    for i, (label, value) in enumerate(fields):
        pdf.info_row(label, value, alt=(i % 2 == 1))
    pdf.ln(6)

    # ── Indices ────────────────────────────────────────────────────────────
    pdf.section_title("INDICES SATELLITAIRES")
    pdf.set_x(10)
    y0 = pdf.get_y()

    ndwi_str  = f"{ndwi:.3f}" if ndwi is not None else "N/A"
    ndvi_str  = f"{ndvi:.3f}" if ndvi is not None else "N/A"
    water_str = f"{water:.2f} km2" if water is not None else "N/A"

    pdf.metric_box("NDWI (indice eau)", ndwi_str, (0, 201, 255))
    pdf.set_xy(pdf.get_x() + 62, y0)
    pdf.metric_box("NDVI (vegetation)", ndvi_str, (0, 229, 160))
    pdf.set_xy(pdf.get_x() + 62, y0)
    pdf.metric_box("Surface eau estimee", water_str, (0, 102, 255))
    pdf.ln(28)

    # ── Risque ────────────────────────────────────────────────────────────
    pdf.section_title("EVALUATION DU RISQUE")
    
    # Nettoyage des emojis pour Helvetica
    clean_risk = risk_level.replace("🟢 ", "").replace("🟠 ", "").replace("🔴 ", "")
    
    risk_colors = {
        "🟢 Faible":   (0, 229, 160),
        "🟠 Moyen":    (255, 149, 0),
        "🔴 Critique": (255, 59, 92),
    }
    r, g, b = risk_colors.get(risk_level, (255, 149, 0))

    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(r, g, b)
    pdf.set_x(10)
    pdf.cell(190, 8, f"Niveau de risque : {clean_risk}   (Score : {risk_score}/100)", ln=True)

    # Barre de risque
    pdf.set_x(10)
    pdf.set_fill_color(26, 34, 53)
    pdf.rect(10, pdf.get_y(), 190, 6, "F")
    bar_w = int(190 * risk_score / 100)
    pdf.set_fill_color(r, g, b)
    pdf.rect(10, pdf.get_y(), bar_w, 6, "F")
    pdf.ln(10)

    # Alertes
    if alerts:
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(255, 143, 163)
        pdf.set_x(10)
        pdf.cell(190, 7, "Alertes detectees :", ln=True)
        pdf.set_font("Helvetica", "", 9)
        for alert in alerts:
            pdf.set_x(14)
            pdf.cell(4, 6, "-")
            pdf.set_text_color(232, 237, 245)
            # Nettoyage des accents pour le texte des alertes
            alert_clean = alert.encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(180, 6, alert_clean)
    else:
        pdf.set_text_color(0, 229, 160)
        pdf.cell(190, 7, "Aucune alerte - etat satisfaisant.", ln=True)

    # ── Export ────────────────────────────────────────────────────────────
    # Avec fpdf2, output() renvoie les bytes directement
    return pdf.output()
    