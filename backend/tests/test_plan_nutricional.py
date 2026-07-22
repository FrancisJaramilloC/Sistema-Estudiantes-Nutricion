"""
Tests for the meal plan with dynamic nutrient calculation (RF9, RF10, RNF2).
Uses mock DynamoDB from conftest.
"""
import uuid


def _seed_alimento(table, alimento_id="alim-001", nombre="Arroz blanco",
                   categoria="Cereales y derivados", energia_kcal=130,
                   proteina_g=2.7, grasa_total_g=0.3, carbohidratos_g=28.2):
    table.put_item(Item={
        "id": alimento_id, "nombre": nombre, "categoria": categoria,
        "energia_kcal": energia_kcal, "proteina_g": proteina_g,
        "grasa_total_g": grasa_total_g, "carbohidratos_g": carbohidratos_g,
        "fibra_g": 0.4, "calcio_mg": 10, "hierro_mg": 0.2,
        "potasio_mg": 35, "sodio_mg": 1, "vitamina_c_mg": 0,
        "vitamina_a_ug": 0, "acido_folico_ug": 3, "vitamina_b12_ug": 0,
    })


class TestCalcularNutrientesPorPorcion:
    """Unit tests for calcular_nutrientes_por_porcion()."""

    def test_calculo_basico_100g(self):
        from app.routes.plan_nutricional import calcular_nutrientes_por_porcion
        alimento = {"energia_kcal": 130, "proteina_g": 2.7, "grasa_total_g": 0.3}
        result = calcular_nutrientes_por_porcion(alimento, 100)
        assert result["energia_kcal"] == 130
        assert result["proteina_g"] == 2.7
        assert result["grasa_total_g"] == 0.3

    def test_calculo_50g(self):
        from app.routes.plan_nutricional import calcular_nutrientes_por_porcion
        alimento = {"energia_kcal": 130, "proteina_g": 2.7}
        result = calcular_nutrientes_por_porcion(alimento, 50)
        assert result["energia_kcal"] == 65.0
        assert result["proteina_g"] == 1.35

    def test_calculo_200g(self):
        from app.routes.plan_nutricional import calcular_nutrientes_por_porcion
        alimento = {"energia_kcal": 130, "carbohidratos_g": 28.2}
        result = calcular_nutrientes_por_porcion(alimento, 200)
        assert result["energia_kcal"] == 260.0
        assert result["carbohidratos_g"] == 56.4

    def test_calculo_valores_null(self):
        from app.routes.plan_nutricional import calcular_nutrientes_por_porcion
        result = calcular_nutrientes_por_porcion({}, 100)
        assert result["energia_kcal"] == 0

    def test_calculo_cantidad_cero(self):
        from app.routes.plan_nutricional import calcular_nutrientes_por_porcion
        alimento = {"energia_kcal": 130}
        result = calcular_nutrientes_por_porcion(alimento, 0)
        assert result["energia_kcal"] == 0


class TestCrearPlanAlimenticio:
    """POST /planes"""

    URL = "/planes"

    def _seed_alimentos(self, client):
        from tests.conftest import _get_fake_table
        table = _get_fake_table("alimentos")
        _seed_alimento(table, "alim-001", "Arroz blanco", energia_kcal=130)
        _seed_alimento(table, "alim-002", "Pollo a la brasa",
                       categoria="Carnes y aves", energia_kcal=239,
                       proteina_g=27.3, grasa_total_g=13.6, carbohidratos_g=0)

    def test_crear_plan_unauthorized(self, client):
        resp = client.post(self.URL, json={
            "paciente_id": "pac-001", "tipo_plan": "Estandar",
            "alimentos": [{"alimento_id": "alim-001", "cantidad_gramos": 200, "comida": "Almuerzo"}]
        })
        assert resp.status_code == 401

    def test_crear_plan_alimentos_invalidos(self, client, auth_header_teacher):
        resp = client.post(self.URL, json={
            "paciente_id": "pac-001", "tipo_plan": "Estandar",
            "alimentos": [{"alimento_id": "no-existe", "cantidad_gramos": 100, "comida": "Almuerzo"}]
        }, headers=auth_header_teacher)
        assert resp.status_code == 404

    def test_crear_plan_exitoso(self, client, auth_header_teacher):
        self._seed_alimentos(client)
        resp = client.post(self.URL, json={
            "paciente_id": "pac-001", "tipo_plan": "Estandar",
            "alimentos": [
                {"alimento_id": "alim-001", "cantidad_gramos": 200, "comida": "Almuerzo"},
                {"alimento_id": "alim-002", "cantidad_gramos": 150, "comida": "Almuerzo"},
            ]
        }, headers=auth_header_teacher)
        assert resp.status_code == 201
        data = resp.json()
        assert "plan_id" in data
        assert len(data["alimentos"]) == 2
        # Arroz 200g: 130*2 = 260 kcal
        assert data["alimentos"][0]["energia_kcal"] == 260.0
        # Pollo 150g: 239*1.5 = 358.5 kcal
        assert data["alimentos"][1]["energia_kcal"] == 358.5
        # Total
        assert data["totales"]["energia_kcal"] == 618.5

    def test_crear_plan_sin_alimentos(self, client, auth_header_student):
        resp = client.post(self.URL, json={
            "paciente_id": "pac-002", "tipo_plan": "Estandar", "alimentos": []
        }, headers=auth_header_student)
        assert resp.status_code == 201
        data = resp.json()
        assert data["totales"]["energia_kcal"] == 0


class TestObtenerPlan:
    """GET /planes/{plan_id}"""

    def _create_plan(self, client, headers):
        from tests.conftest import _get_fake_table
        table = _get_fake_table("alimentos")
        _seed_alimento(table)
        resp = client.post("/planes", json={
            "paciente_id": "pac-001", "tipo_plan": "Estandar",
            "alimentos": [{"alimento_id": "alim-001", "cantidad_gramos": 100, "comida": "Almuerzo"}]
        }, headers=headers)
        return resp.json()["plan_id"]

    def test_obtener_plan_no_encontrado(self, client, auth_header_teacher):
        resp = client.get(f"/planes/{uuid.uuid4()}", headers=auth_header_teacher)
        assert resp.status_code == 404

    def test_obtener_plan_exitoso(self, client, auth_header_teacher):
        plan_id = self._create_plan(client, auth_header_teacher)
        resp = client.get(f"/planes/{plan_id}", headers=auth_header_teacher)
        assert resp.status_code == 200
        data = resp.json()
        assert data["plan_id"] == plan_id
        assert data["paciente_id"] == "pac-001"


class TestPlanesPorPaciente:
    """GET /planes/paciente/{paciente_id}"""

    def test_paciente_sin_planes(self, client, auth_header_teacher):
        resp = client.get(f"/planes/paciente/pac-sin-planes", headers=auth_header_teacher)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0

    def test_paciente_con_planes(self, client, auth_header_teacher):
        from tests.conftest import _get_fake_table
        table = _get_fake_table("alimentos")
        _seed_alimento(table)
        client.post("/planes", json={
            "paciente_id": "pac-planes", "tipo_plan": "Estandar",
            "alimentos": [{"alimento_id": "alim-001", "cantidad_gramos": 100, "comida": "Almuerzo"}]
        }, headers=auth_header_teacher)
        resp = client.get("/planes/paciente/pac-planes", headers=auth_header_teacher)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["planes"][0]["paciente_id"] == "pac-planes"


class TestCalcularPorcion:
    """POST /planes/calcular-porcion"""

    def test_calcular_porcion(self, client, auth_header_teacher):
        from tests.conftest import _get_fake_table
        table = _get_fake_table("alimentos")
        _seed_alimento(table, energia_kcal=130)
        resp = client.post("/planes/calcular-porcion?alimento_id=alim-001&cantidad_gramos=50",
                           headers=auth_header_teacher)
        assert resp.status_code == 200
        data = resp.json()
        assert data["energia_kcal"] == 65.0

    def test_calcular_porcion_alimento_no_encontrado(self, client, auth_header_teacher):
        resp = client.post("/planes/calcular-porcion?alimento_id=no-existe&cantidad_gramos=50",
                           headers=auth_header_teacher)
        assert resp.status_code == 404


class TestEliminarPlan:
    """DELETE /planes/{plan_id}"""

    def test_eliminar_plan_student_forbidden(self, client, auth_header_student):
        from tests.conftest import _get_fake_table
        table = _get_fake_table("alimentos")
        _seed_alimento(table)
        create_resp = client.post("/planes", json={
            "paciente_id": "pac-001", "tipo_plan": "Estandar",
            "alimentos": [{"alimento_id": "alim-001", "cantidad_gramos": 100, "comida": "Almuerzo"}]
        }, headers=auth_header_student)
        plan_id = create_resp.json()["plan_id"]
        resp = client.delete(f"/planes/{plan_id}", headers=auth_header_student)
        assert resp.status_code == 403

    def test_eliminar_plan_docente(self, client, auth_header_teacher):
        from tests.conftest import _get_fake_table
        table = _get_fake_table("alimentos")
        _seed_alimento(table)
        create_resp = client.post("/planes", json={
            "paciente_id": "pac-001", "tipo_plan": "Estandar",
            "alimentos": [{"alimento_id": "alim-001", "cantidad_gramos": 100, "comida": "Almuerzo"}]
        }, headers=auth_header_teacher)
        plan_id = create_resp.json()["plan_id"]
        resp = client.delete(f"/planes/{plan_id}", headers=auth_header_teacher)
        assert resp.status_code == 200
        assert "eliminado" in resp.json()["mensaje"]

    def test_eliminar_plan_no_encontrado(self, client, auth_header_teacher):
        resp = client.delete(f"/planes/{uuid.uuid4()}", headers=auth_header_teacher)
        assert resp.status_code == 404
