#!/usr/bin/env python3
"""
Extrae la tabla de composición de alimentos del PDF "Tabla de composición de los alimentos SF"
y genera un archivo JSON normalizado para carga en DynamoDB.

RFC: RF9, RF12, RNF14, RES2
Fuente: Tabla de composición química de los alimentos - USFQ (Diciembre 2021)
"""

import json
import re
import pdfplumber
import os

PDF_PATH = os.path.join(os.path.dirname(__file__), "..", "Tabla de composicion de los alimentos SF.pdf")
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "alimentos_usfq.json")

# Columnas en el orden correcto del PDF original (antes del espejado)
COLUMN_HEADERS = [
    "fuente",           # Fuente / categoría
    "alimento",         # Nombre del alimento
    "nombre_ingles",    # Nombre en inglés
    "energia_kcal",     # Energía calórica (Kcal)
    "proteina_g",       # Proteína (g)
    "grasa_total_g",    # Grasa total (g)
    "carbohidratos_g",  # Carbohidratos (g)
    "fibra_g",          # Fibra (g)
    "aga_g",            # AGA - Ácidos grasos saturados (g)
    "aga_mono_g",       # AGA Monoinsaturados (g)
    "aga_poly_g",       # AGA Poliinsaturados (g)
    "colesterol_mg",    # Colesterol (mg)
    "calcio_mg",        # Calcio (mg)
    "fosforo_mg",       # Fósforo (mg)
    "hierro_mg",        # Hierro (mg)
    "potasio_mg",       # Potasio (mg)
    "sodio_mg",         # Sodio (mg)
    "zinc_mg",          # Zinc (mg)
    "vitamina_c_mg",    # Vitamina C (mg)
    "vitamina_a_ug",    # Vitamina A (µg ERE)
    "acido_folico_ug",  # Ácido fólico (µg)
    "vitamina_b12_ug",  # Vitamina B12 (µg)
]


def parse_number(val):
    """Convierte un string con formato ecuatoriano (coma decimal) a float."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    val = str(val).strip()
    val = val.replace("\n", " ").strip()
    if not val or val == "" or val == "-":
        return None
    # Replace comma decimal separator
    val = val.replace(",", ".")
    try:
        return float(val)
    except ValueError:
        return None


def classify_food(name, category_hint):
    """Clasifica un alimento en una categoría basada en su nombre y la categoría de la tabla."""
    name_lower = name.lower()

    # Mapeo directo de categorías del PDF
    cat_map = {
        "cereales": "Cereales y derivados",
        "plátano": "Plátanos y tubérculos",
        "tubérculo": "Plátanos y tubérculos",
        "legumbre": "Legumbres y derivados",
        "fréjol": "Legumbres y derivados",
        "fréjol": "Legumbres y derivados",
        "arveja": "Legumbres y derivados",
        "lenteja": "Legumbres y derivados",
        "haba": "Legumbres y derivados",
        "quinua": "Cereales y derivados",
        "avena": "Cereales y derivados",
        "trigo": "Cereales y derivados",
        "arroz": "Cereales y derivados",
        "maíz": "Cereales y derivados",
        "pan": "Cereales y derivados",
        "pasta": "Cereales y derivados",
        "harina": "Cereales y derivados",
        "chocolate": "Azúcares y dulces",
        "dulce": "Azúcares y dulces",
        "mermelada": "Azúcares y dulces",
        "azúcar": "Azúcares y dulces",
        "gaseosa": "Bebidas",
        "jugo": "Bebidas",
        "bebida": "Bebidas",
        "cerveza": "Bebidas",
        "vino": "Bebidas",
        "café": "Bebidas",
        "té": "Bebidas",
        "aceite": "Grasas y aceites",
        "mantequilla": "Grasas y aceites",
        "margarina": "Grasas y aceites",
        "crema agria": "Lácteos y derivados",
        "leche": "Lácteos y derivados",
        "queso": "Lácteos y derivados",
        "yogurt": "Lácteos y derivados",
        "helado": "Lácteos y derivados",
        "huevo": "Huevos",
        "pollo": "Carnes y aves",
        "res": "Carnes y aves",
        "cerdo": "Carnes y aves",
        "borrego": "Carnes y aves",
        "carne": "Carnes y aves",
        "atún": "Pescados y mariscos",
        "salmón": "Pescados y mariscos",
        "camarón": "Pescados y mariscos",
        "langostino": "Pescados y mariscos",
        "almeja": "Pescados y mariscos",
        "pescado": "Pescados y mariscos",
        "manzana": "Frutas",
        "plátano": "Frutas",
        "naranja": "Frutas",
        "pera": "Frutas",
        "uva": "Frutas",
        "fresa": "Frutas",
        "mango": "Frutas",
        "papaya": "Frutas",
        "piña": "Frutas",
        "aguacate": "Frutas",
        "coco": "Frutas",
        "limón": "Frutas",
        "sandía": "Frutas",
        "melón": "Frutas",
        "ciruela": "Frutas",
        "grosella": "Frutas",
        "tomate": "Verduras y hortalizas",
        "cebolla": "Verduras y hortalizas",
        "lechuga": "Verduras y hortalizas",
        "zanahoria": "Verduras y hortalizas",
        "papa": "Verduras y hortalizas",
        "choclo": "Verduras y hortalizas",
        "acelga": "Verduras y hortalizas",
        "espinaca": "Verduras y hortalizas",
        "brócoli": "Verduras y hortalizas",
        "rúcula": "Verduras y hortalizas",
        "palmito": "Verduras y hortalizas",
        "semilla": "Frutos secos y semillas",
        "nuez": "Frutos secos y semillas",
        "almendra": "Frutos secos y semillas",
        "maní": "Frutos secos y semillas",
        "ajonjolí": "Frutos secos y semillas",
        "confite": "Snacks y dulces",
        "papa frita": "Snacks y dulces",
        "palomitas": "Snacks y dulces",
        "galleta": "Snacks y dulces",
        "bizcocho": "Snacks y dulces",
    }

    # Check category_hint first
    if category_hint:
        hint_lower = category_hint.lower()
        if "cereal" in hint_lower:
            return "Cereales y derivados"
        if "plátano" in hint_lower or "tubérculo" in hint_lower:
            return "Plátanos y tubérculos"
        if "legumbre" in hint_lower:
            return "Legumbres y derivados"
        if "fruta" in hint_lower:
            return "Frutas"
        if "verdura" in hint_lower or "hortaliza" in hint_lower:
            return "Verduras y hortalizas"
        if "carne" in hint_lower or "ave" in hint_lower:
            return "Carnes y aves"
        if "pescado" in hint_lower or "marisco" in hint_lower:
            return "Pescados y mariscos"
        if "lácteo" in hint_lower or "leche" in hint_lower:
            return "Lácteos y derivados"
        if "huevo" in hint_lower:
            return "Huevos"
        if "grasa" in hint_lower or "aceite" in hint_lower:
            return "Grasas y aceites"
        if "azúcar" in hint_lower or "dulce" in hint_lower:
            return "Azúcares y dulces"
        if "bebida" in hint_lower:
            return "Bebidas"
        if "snack" in hint_lower:
            return "Snacks y dulces"
        if "semilla" in hint_lower or "nuez" in hint_lower:
            return "Frutos secos y semillas"

    # Fallback to name matching
    for key, cat in cat_map.items():
        if key in name_lower:
            return cat

    return "Otros"


def extract_alimentos_from_pdf(pdf_path):
    """Extrae todos los alimentos del PDF y retorna una lista de diccionarios."""
    alimentos = []
    pdf = pdfplumber.open(pdf_path)
    current_category = None

    for page_idx, page in enumerate(pdf.pages):
        tables = page.extract_tables()
        for table in tables:
            if not table or len(table) < 3:
                continue

            # Check header row to identify food tables
            header = table[0]
            if not header:
                continue

            header_text = " ".join(str(c or "") for c in header).lower()

            # Skip non-food tables (like the nutrient list table on page 9)
            if "nutriente" in header_text and "unidad" in header_text and "abreviatura" in header_text:
                continue

            # Check if this is a data table with food entries
            has_alimento_col = False
            for cell in header:
                if cell and ("alimento" in str(cell).lower() or "fuente" in str(cell).lower()):
                    has_alimento_col = True
                    break

            if not has_alimento_col:
                continue

            # Process data rows (skip header rows which are rows 0 and 1)
            for row_idx in range(2, len(table)):
                row = table[row_idx]
                if not row or len(row) < 6:
                    continue

                # Column 0 is the reversed "Fuente" - category or number
                # Column 1 is the food name
                # Column 2 is English name
                # Columns 3-21 are nutrients

                food_name = str(row[1] or "").strip().replace("\n", " ")
                if not food_name:
                    # This might be a category header row
                    col0 = str(row[0] or "").strip()
                    if col0 and not col0.isdigit():
                        # Could be a category
                        current_category = col0
                    continue

                # Check if col0 is a number (food item number) or category name
                col0 = str(row[0] or "").strip()

                # Skip if food_name looks like a header repetition
                if food_name.lower() in ["alimento", "fuente", "nutriente"]:
                    continue

                # Extract nutrients
                nutrients = {}
                for i in range(3, min(len(row), len(COLUMN_HEADERS))):
                    val = parse_number(row[i])
                    nutrients[COLUMN_HEADERS[i]] = val

                alimento = {
                    "nombre": food_name,
                    "nombre_ingles": str(row[2] or "").strip().replace("\n", " "),
                    "categoria": classify_food(food_name, current_category),
                    "fuente_tabla": "USFQ - Tabla de composición de alimentos (2021)",
                }
                alimento.update(nutrients)
                alimentos.append(alimento)

    pdf.close()
    return alimentos


def main():
    print(f"Extrayendo alimentos de: {PDF_PATH}")
    alimentos = extract_alimentos_from_pdf(PDF_PATH)
    print(f"Total de alimentos extraídos: {len(alimentos)}")

    # Add sequential IDs
    for i, al in enumerate(alimentos):
        al["id"] = f"ALIM-{i+1:04d}"

    # Print category distribution
    categories = {}
    for al in alimentos:
        cat = al["categoria"]
        categories[cat] = categories.get(cat, 0) + 1
    print("\nDistribución por categoría:")
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count}")

    # Print sample
    print("\nMuestra (primeros 3 alimentos):")
    for al in alimentos[:3]:
        print(json.dumps(al, indent=2, ensure_ascii=False))

    # Save to JSON
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(alimentos, f, indent=2, ensure_ascii=False)
    print(f"\nJSON guardado en: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
