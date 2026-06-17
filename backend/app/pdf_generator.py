import os
from io import BytesIO
from fpdf import FPDF

_LOGO_PATH = os.path.join(os.path.dirname(__file__), "nutria-logo.png")

class PlanPDF(FPDF):
    def header(self):
        if os.path.exists(_LOGO_PATH):
            self.image(_LOGO_PATH, x=10, y=6, w=50, h=50)

        self.set_text_color(30, 63, 32)
        self.set_font("Helvetica", "B", 18)
        self.set_xy(68, 16)
        self.cell(0, 10, "NUTRIA", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 10)
        self.set_xy(68, 30)
        self.cell(0, 8, "Plan Nutricional Personalizado", new_x="LMARGIN", new_y="NEXT")

        self.ln(22)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 110, 90)
        self.cell(0, 10, f"Pagina {self.page_no()}/{{nb}}", align="C")

def generar_pdf_plan(tarea: dict) -> BytesIO:
    pdf = PlanPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(60, 60, 60)

    row = lambda label, value: f"{label}: {value or 'N/A'}"

    info = [
        ("Paciente", tarea.get("paciente_id")),
        ("Tipo de Plan", tarea.get("tipo_plan")),
        ("Estado", tarea.get("estado_actual")),
        ("Creado", tarea.get("created_at")),
        ("Actualizado", tarea.get("updated_at")),
        ("Finalizado", tarea.get("finished_at")),
    ]

    for label, value in info:
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(50, 8, label + ":", align="R")
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 8, str(value or "N/A"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    alimentos = tarea.get("alimentos", [])
    if alimentos:
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(30, 63, 32)
        pdf.cell(0, 10, "Menu Diario", new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(60, 60, 60)

        comidas = ["Desayuno", "Almuerzo", "Cena", "Colacion"]
        for comida in comidas:
            items = [a for a in alimentos if a.get("comida", "").lower() == comida.lower()]
            if not items:
                continue
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_fill_color(240, 245, 240)
            pdf.cell(0, 8, comida, new_x="LMARGIN", new_y="NEXT", fill=True)
            pdf.set_font("Helvetica", "", 10)
            for item in items:
                nombre = item.get("nombre", "")
                cantidad = item.get("cantidad", "")
                pdf.cell(10, 7, "")
                pdf.cell(0, 7, f"{nombre} ({cantidad})", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)
    else:
        pdf.set_font("Helvetica", "I", 10)
        pdf.set_text_color(150, 150, 150)
        pdf.cell(0, 10, "Sin alimentos registrados.", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(6)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(120, 110, 90)
    pdf.cell(0, 10, "Documento generado por NUTRIA - Sistema de Gestion Integral para Estudiantes de Nutricion", new_x="LMARGIN", new_y="NEXT", align="C")

    buf = BytesIO()
    pdf.output(buf)
    buf.seek(0)
    return buf
