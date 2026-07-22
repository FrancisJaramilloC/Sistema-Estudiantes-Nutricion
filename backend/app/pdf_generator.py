import os
from io import BytesIO
from fpdf import FPDF

_LOGO_PATH = os.path.join(os.path.dirname(__file__), "nutria-logo.png")

COMIDAS_ORDEN = ["Desayuno", "Almuerzo", "Cena", "Colacion"]

NUTRIENTES_TABLA = [
    ("Energia", "energia_kcal", "kcal"),
    ("Proteina", "proteina_g", "g"),
    ("Grasa Total", "grasa_total_g", "g"),
    ("Carbohidratos", "carbohidratos_g", "g"),
    ("Fibra", "fibra_g", "g"),
    ("Calcio", "calcio_mg", "mg"),
    ("Hierro", "hierro_mg", "mg"),
    ("Potasio", "potasio_mg", "mg"),
    ("Sodio", "sodio_mg", "mg"),
    ("Vitamina C", "vitamina_c_mg", "mg"),
    ("Vitamina A", "vitamina_a_ug", "ug"),
    ("Ac. Folico", "acido_folico_ug", "ug"),
    ("Vitamina B12", "vitamina_b12_ug", "ug"),
]

MACROS = [
    ("Proteina", "proteina_g", "g"),
    ("Grasa Total", "grasa_total_g", "g"),
    ("Carbohidratos", "carbohidratos_g", "g"),
]


class PlanPDF(FPDF):
    def header(self):
        if os.path.exists(_LOGO_PATH):
            try:
                self.image(_LOGO_PATH, x=10, y=6, w=50, h=50)
            except Exception:
                pass

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

    def section_title(self, title):
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(30, 63, 32)
        self.set_fill_color(230, 245, 230)
        self.cell(0, 9, f"  {title}", new_x="LMARGIN", new_y="NEXT", fill=True)
        self.ln(3)

    def info_row(self, label, value):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(60, 60, 60)
        self.cell(55, 7, label + ":", align="R")
        self.set_font("Helvetica", "", 10)
        self.cell(0, 7, f"  {value or 'N/D'}", new_x="LMARGIN", new_y="NEXT")


def _fmt(val, decimales=1):
    if val is None:
        return "N/D"
    if isinstance(val, float):
        return f"{val:.{decimales}f}"
    return str(val)


def calcular_macros_totales(totales):
    prot = totales.get("proteina_g") or 0
    grasa = totales.get("grasa_total_g") or 0
    carbs = totales.get("carbohidratos_g") or 0
    total_kcal = (prot * 4) + (grasa * 9) + (carbs * 4)
    if total_kcal == 0:
        return 0, 0, 0, 0
    return total_kcal, (prot * 4 / total_kcal) * 100, (grasa * 9 / total_kcal) * 100, (carbs * 4 / total_kcal) * 100


def generar_pdf_plan(tarea: dict) -> BytesIO:
    """Genera PDF a partir del formato antiguo (tasks table)."""
    pdf = PlanPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(60, 60, 60)

    pdf.section_title("Informacion del Plan")
    info = [
        ("Paciente", tarea.get("paciente_id")),
        ("Tipo de Plan", tarea.get("tipo_plan")),
        ("Estado", tarea.get("estado_actual")),
        ("Creado", tarea.get("created_at")),
        ("Actualizado", tarea.get("updated_at")),
    ]
    for label, value in info:
        pdf.info_row(label, value)
    pdf.ln(5)

    alimentos = tarea.get("alimentos", [])
    if alimentos:
        pdf.section_title("Menu Diario")
        comidas = ["Desayuno", "Almuerzo", "Cena", "Colacion"]
        for comida in comidas:
            items = [a for a in alimentos if a.get("comida", "").lower() == comida.lower()]
            if not items:
                continue
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(30, 63, 32)
            pdf.cell(0, 8, comida, new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(60, 60, 60)
            for item in items:
                nombre = item.get("nombre", "")
                cantidad = item.get("cantidad_gramos") or item.get("cantidad", "")
                pdf.cell(10, 7, "")
                pdf.cell(0, 7, f"- {nombre} ({cantidad}g)", new_x="LMARGIN", new_y="NEXT")
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


def generar_pdf_plan_nutricional(plan: dict) -> BytesIO:
    """
    Genera un PDF completo con toda la informacion del plan alimenticio:
    - Datos del paciente y metadatos del plan
    - Distribucion de macronutrientes (% y gramos)
    - Totales diarios de macro/micronutrientes
    - Desglose por comida (Desayuno, Almuerzo, Cena, Colacion) con nutrientes
    """
    pdf = PlanPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(60, 60, 60)

    pdf.section_title("Informacion del Plan")
    info = [
        ("Paciente", plan.get("paciente_id")),
        ("Tipo de Plan", plan.get("tipo_plan")),
        ("Estado", plan.get("estado")),
        ("Creado por", plan.get("created_by")),
        ("Fecha de creacion", plan.get("created_at")),
    ]
    for label, value in info:
        pdf.info_row(label, value)
    pdf.ln(5)

    totales = plan.get("totales", {})
    kcal_total, pct_prot, pct_grasa, pct_carbs = calcular_macros_totales(totales)

    pdf.section_title("Distribucion de Macronutrientes")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(60, 60, 60)

    prot_g = totales.get("proteina_g") or 0
    grasa_g = totales.get("grasa_total_g") or 0
    carbs_g = totales.get("carbohidratos_g") or 0

    macro_data = [
        ("Energia Total", f"{_fmt(kcal_total, 0)} kcal"),
        ("Proteina", f"{_fmt(prot_g)}g  ({_fmt(pct_prot, 1)}%)"),
        ("Grasa Total", f"{_fmt(grasa_g)}g  ({_fmt(pct_grasa, 1)}%)"),
        ("Carbohidratos", f"{_fmt(carbs_g)}g  ({_fmt(pct_carbs, 1)}%)"),
    ]
    for label, value in macro_data:
        pdf.info_row(label, value)
    pdf.ln(5)

    pdf.section_title("Totales Diarios de Nutrientes")

    col_w = [70, 40, 30]
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(30, 63, 32)
    pdf.set_fill_color(230, 245, 230)
    for ci, h in enumerate(["Nutriente", "Valor", "Unidad"]):
        pdf.cell(col_w[ci], 7, h, border=1, fill=True, align="C")
    pdf.ln()

    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(60, 60, 60)
    for i, (label, key, unit) in enumerate(NUTRIENTES_TABLA):
        if i % 2 == 0:
            pdf.set_fill_color(245, 250, 245)
        else:
            pdf.set_fill_color(255, 255, 255)
        pdf.cell(col_w[0], 6, label, border=1, align="L", fill=True)
        pdf.cell(col_w[1], 6, _fmt(totales.get(key)), border=1, align="R", fill=True)
        pdf.cell(col_w[2], 6, unit, border=1, align="C", fill=True)
        pdf.ln()
    pdf.ln(5)

    alimentos = plan.get("alimentos", [])
    if alimentos:
        pdf.section_title("Desglose por Comida")

        for comida in COMIDAS_ORDEN:
            items = [a for a in alimentos if a.get("comida", "").lower() == comida.lower()]
            if not items:
                continue

            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(30, 63, 32)
            pdf.set_fill_color(240, 245, 240)
            total_comida_kcal = sum((a.get("energia_kcal") or 0) for a in items)
            pdf.cell(0, 8, f"  {comida}  ({len(items)} alimentos - {_fmt(total_comida_kcal, 0)} kcal)", new_x="LMARGIN", new_y="NEXT", fill=True)
            pdf.ln(1)

            t_cols = [65, 18, 20, 20, 20, 20]
            pdf.set_font("Helvetica", "B", 7)
            pdf.set_text_color(30, 63, 32)
            pdf.set_fill_color(245, 250, 245)
            for ci, h in enumerate(["Alimento", "Gramos", "Kcal", "Prot.", "Grasa", "Carbs"]):
                pdf.cell(t_cols[ci], 6, h, border=1, fill=True, align="C")
            pdf.ln()

            pdf.set_font("Helvetica", "", 7)
            pdf.set_text_color(60, 60, 60)
            for item in items:
                nombre = item.get("nombre", "")
                if len(nombre) > 32:
                    nombre = nombre[:30] + ".."
                pdf.cell(t_cols[0], 6, nombre, border=1, align="L")
                pdf.cell(t_cols[1], 6, _fmt(item.get("cantidad_gramos"), 0), border=1, align="R")
                pdf.cell(t_cols[2], 6, _fmt(item.get("energia_kcal")), border=1, align="R")
                pdf.cell(t_cols[3], 6, _fmt(item.get("proteina_g")), border=1, align="R")
                pdf.cell(t_cols[4], 6, _fmt(item.get("grasa_total_g")), border=1, align="R")
                pdf.cell(t_cols[5], 6, _fmt(item.get("carbohidratos_g")), border=1, align="R")
                pdf.ln()

            subtotales = {
                "energia_kcal": sum((a.get("energia_kcal") or 0) for a in items),
                "proteina_g": sum((a.get("proteina_g") or 0) for a in items),
                "grasa_total_g": sum((a.get("grasa_total_g") or 0) for a in items),
                "carbohidratos_g": sum((a.get("carbohidratos_g") or 0) for a in items),
            }
            pdf.set_font("Helvetica", "B", 7)
            pdf.set_fill_color(235, 245, 235)
            pdf.cell(t_cols[0], 6, "Subtotal", border=1, fill=True, align="L")
            pdf.cell(t_cols[1], 6, "", border=1, fill=True)
            pdf.cell(t_cols[2], 6, _fmt(subtotales["energia_kcal"]), border=1, fill=True, align="R")
            pdf.cell(t_cols[3], 6, _fmt(subtotales["proteina_g"]), border=1, fill=True, align="R")
            pdf.cell(t_cols[4], 6, _fmt(subtotales["grasa_total_g"]), border=1, fill=True, align="R")
            pdf.cell(t_cols[5], 6, _fmt(subtotales["carbohidratos_g"]), border=1, fill=True, align="R")
            pdf.ln(6)
    else:
        pdf.set_font("Helvetica", "I", 10)
        pdf.set_text_color(150, 150, 150)
        pdf.cell(0, 10, "Sin alimentos registrados en el plan.", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(4)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(120, 110, 90)
    pdf.cell(0, 10, "Documento generado por NUTRIA - Sistema de Gestion Integral para Estudiantes de Nutricion", new_x="LMARGIN", new_y="NEXT", align="C")

    buf = BytesIO()
    pdf.output(buf)
    buf.seek(0)
    return buf
