"""
Tests for app.pdf_generator — validates PDF generation from plan data.

These tests verify the function runs without errors and produces valid PDF content.
"""

from app.pdf_generator import generar_pdf_plan


class TestGenerarPdfPlan:
    def test_minimal_plan(self):
        """A plan with minimal data should produce a valid PDF."""
        task = {
            "paciente_id": "pat-001",
            "tipo_plan": "Estandar",
            "estado_actual": "COMPLETADO",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T01:00:00",
        }
        buf = generar_pdf_plan(task)
        data = buf.read()
        assert len(data) > 0
        assert data.startswith(b"%PDF")  # Valid PDF header

    def test_plan_with_alimentos(self):
        """A plan with food items should produce a valid PDF."""
        task = {
            "paciente_id": "pat-002",
            "tipo_plan": "Cetogenico",
            "estado_actual": "COMPLETADO",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T01:00:00",
            "alimentos": [
                {"nombre": "Huevos revueltos", "cantidad": "3 unidades", "comida": "Desayuno"},
                {"nombre": "Ensalada de pollo", "cantidad": "1 plato", "comida": "Almuerzo"},
                {"nombre": "Salmón a la plancha", "cantidad": "200g", "comida": "Cena"},
            ],
        }
        buf = generar_pdf_plan(task)
        data = buf.read()
        assert len(data) > 0
        assert data.startswith(b"%PDF")

    def test_plan_with_multiple_meals(self):
        """A plan covering all meal types should produce a valid PDF."""
        task = {
            "paciente_id": "pat-003",
            "tipo_plan": "Hipercalorico",
            "estado_actual": "PENDIENTE",
            "alimentos": [
                {"nombre": "Avena", "cantidad": "1 taza", "comida": "Desayuno"},
                {"nombre": "Batido", "cantidad": "500ml", "comida": "Colacion"},
                {"nombre": "Pasta", "cantidad": "1 plato", "comida": "Almuerzo"},
                {"nombre": "Fruta", "cantidad": "2 piezas", "comida": "Colacion"},
                {"nombre": "Pescado", "cantidad": "200g", "comida": "Cena"},
            ],
        }
        buf = generar_pdf_plan(task)
        data = buf.read()
        assert len(data) > 0
        assert data.startswith(b"%PDF")

    def test_null_values_handled(self):
        """A plan with None values should not crash."""
        task = {
            "paciente_id": None,
            "tipo_plan": None,
            "estado_actual": None,
            "created_at": None,
            "updated_at": None,
            "finished_at": None,
        }
        buf = generar_pdf_plan(task)
        data = buf.read()
        assert len(data) > 0
        assert data.startswith(b"%PDF")
