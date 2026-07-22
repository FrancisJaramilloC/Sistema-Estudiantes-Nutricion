"""
Tests for app.models — validates Pydantic model serialization/validation.
"""

from app.models import FoodItem, PlanRequest


class TestFoodItem:
    def test_basic_food_item(self):
        item = FoodItem(nombre="Arroz", cantidad="200g", comida="Almuerzo")
        assert item.nombre == "Arroz"
        assert item.cantidad == "200g"
        assert item.comida == "Almuerzo"

    def test_food_item_serialization(self):
        item = FoodItem(nombre="Pollo", cantidad="150g", comida="Cena")
        data = item.model_dump()
        assert data == {"nombre": "Pollo", "cantidad": "150g", "comida": "Cena"}


class TestPlanRequest:
    def test_empty_alimentos(self):
        req = PlanRequest(paciente_id="pat-001", tipo_plan="Estandar")
        assert req.paciente_id == "pat-001"
        assert req.tipo_plan == "Estandar"
        assert req.alimentos == []

    def test_with_alimentos(self):
        foods = [
            FoodItem(nombre="Avena", cantidad="1 taza", comida="Desayuno"),
            FoodItem(nombre="Ensalada", cantidad="1 plato", comida="Almuerzo"),
        ]
        req = PlanRequest(paciente_id="pat-002", tipo_plan="Cetogenico", alimentos=foods)
        assert len(req.alimentos) == 2

    def test_serialization_to_dict(self):
        req = PlanRequest(paciente_id="pat-003", tipo_plan="Hipercalorico")
        data = req.model_dump()
        assert data["paciente_id"] == "pat-003"
        assert data["tipo_plan"] == "Hipercalorico"
        assert data["alimentos"] == []
