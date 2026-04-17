from fpdf import FPDF
import io
from datetime import datetime

class BarragePDF(FPDF):
    def header(self):
        # Fond du header (Bleu foncé comme le dashboard)
        self.set_fill_color(10, 14, 26)
        self.rect(0, 0, 210, 30, "F")
        
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(0, 201, 255)
        self.set_xy(10, 8)
        self.cell(0, 10, "DASHBOARD BARRAGES MAROC", ln=False)
        
        self.set_font("Helvetica", "", 8)
        self.set_text_color(107, 127, 163)
        self.set_xy(10, 20)
        self.cell(0, 6, f"Rapport genere le {datetime.now().strftime('%d/%m/%Y a %H:%M')}")
        self.ln(18)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(107, 127, 163)
        self.cell(0, 10, f"Page {self.page_no()} | Systeme de Surveillance SIG - Hajar", align="C")

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
        val_clean = str(value).encode('latin-1', 'ignore').decode('latin-1')
        self.cell(120, 7, val_clean, fill=True, ln=True)

    def metric_box(self, label, value, color_rgb=(0, 201, 255), width=45):
        x, y = self.get_x(), self.get_y()
        self.set_fill_color(26, 34, 53)
        self.rect(x, y, width, 22, "F")
        self.set_font("Helvetica", "", 7)
        self.set_text_color(107, 127, 163)
        self.set_xy(x + 2, y + 3)
        self.cell(width-4, 5, label)
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(*color_rgb)
        self.set_xy(x + 2, y + 10)
        self.cell(width-4, 10, str(value), align="C")

def generate_pdf(barrage_name, row, ndwi, ndvi, water,
                  risk_level, risk_score, alerts, start, end, ndti=None): # Ajout ndti
    
    pdf = BarragePDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # --- Titre barrage ---
    pdf.set_fill_color(0, 102, 255)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 14)
    b_name_clean = str(barrage_name).encode('latin-1', 'ignore').decode('latin-1')
    pdf.cell(190, 12, f"   Barrage : {b_name_clean}", fill=True, ln=True)
    pdf.ln(2)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(107, 127, 163)
    pdf.cell(190, 6, f"Periode d'analyse : {start} au {end}", ln=True)
    pdf.ln(4)

    # --- Fiche technique ---
    pdf.section_title("FICHE TECHNIQUE")
    fields = [
        ("Capacite (Mm3)",   row.get("capacite", "—")),
        ("Region",           row.get("nom_region", "—")),
        ("Province",         row.get("nom_provin", "—")),
        ("Bassin",           row.get("bassin", "—")),
        ("Coordonnees",      f"{row.get('lat','—')} N, {row.get('lon','—')} E"),
    ]
    for i, (label, value) in enumerate(fields):
        pdf.info_row(label, value, alt=(i % 2 == 1))
    pdf.ln(6)

    # --- Indices (4 boîtes maintenant) ---
    pdf.section_title("INDICES SATELLITAIRES (SENTINEL-2)")
    y0 = pdf.get_y()
    
    ndwi_s  = f"{ndwi:.3f}" if ndwi is not None else "N/A"
    ndvi_s  = f"{ndvi:.3f}" if ndvi is not None else "N/A"
    ndti_s  = f"{ndti:.3f}" if ndti is not None else "N/A"
    water_s = f"{water:.2f} km2" if water is not None else "N/A"

    pdf.set_x(10)
    pdf.metric_box("NDWI (Eau)", ndwi_s, (0, 201, 255))
    pdf.set_xy(58, y0)
    pdf.metric_box("NDTI (Turbidite)", ndti_s, (255, 149, 0)) # Nouvelle boîte
    pdf.set_xy(106, y0)
    pdf.metric_box("NDVI (Vegetation)", ndvi_s, (0, 229, 160))
    pdf.set_xy(154, y0)
    pdf.metric_box("Surface", water_s, (232, 237, 245))
    pdf.ln(28)

    # --- Risque ---
    pdf.section_title("EVALUATION DU RISQUE ET ALERTES")
    clean_risk = str(risk_level).replace("🟢 ", "").replace("🟠 ", "").replace("🔴 ", "")
    risk_colors = {"Faible": (0, 229, 160), "Moyen": (255, 149, 0), "Critique": (255, 59, 92)}
    r, g, b = risk_colors.get(clean_risk, (255, 149, 0))

    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(r, g, b)
    pdf.cell(190, 8, f"Niveau de risque global : {clean_risk}   (Score : {risk_score}/100)", ln=True)

    # Barre de progression
    pdf.set_fill_color(26, 34, 53)
    pdf.rect(10, pdf.get_y(), 190, 3, "F")
    pdf.set_fill_color(r, g, b)
    pdf.rect(10, pdf.get_y(), int(190 * risk_score / 100), 3, "F")
    pdf.ln(10)

    # Alertes
    if alerts:
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(255, 143, 163)
        pdf.cell(190, 7, "Alertes techniques detectees :", ln=True)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(232, 237, 245)
        for alert in alerts:
            a_clean = alert.encode('latin-1', 'ignore').decode('latin-1').replace("🚨", "").replace("⚠️", "").replace("🌫️", "").replace("💧", "")
            pdf.set_x(14)
            pdf.multi_cell(180, 6, f"- {a_clean}")
    
    return pdf.output()