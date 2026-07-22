"""
Tests for automatic plan suggestion routes (RF5, RF11, RF7).
Uses mock DynamoDB from conftest.
"""
import uuid


def _seed_alimentos_bulk(table):
    """Seed multiple foods across categories for suggestion tests."""
    foods = [
        {"id": "c1", "nombre": "Arroz", "categoria": "Cereales y derivados",
         "energia_kcal": 130, "proteina_g": 2.7, "grasa_total_g": 0.3, "carbohidratos_g": 28},
        {"id": "c2", "nombre": "Avena", "categoria": "Cereales y derivados",
         "energia_kcal": 389, "proteina_g": 16.9, "grasa_total_g": 6.9, "carbohidratos_g": 66},
        {"id": "f1", "nombre": "Manzana", "categoria": "Frutas",
         "energia_kcal": 52, "proteina_g": 0.3, "grasa_total_g": 0.2, "carbohidratos_g": 14},
        {"id": "f2", "nombre": "Plátano", "categoria": "Frutas",
         "energia_kcal": 93, "proteina_g": 1.1, "grasa_total_g": 0.3, "carbohidratos_g": 23},
        {"id": "v1", "nombre": "Brócoli", "categoria": "Verduras y hortalizas",
         "energia_kcal": 34, "proteina_g": 2.8, "grasa_total_g": 0.4, "carbohidratos_g": 7},
        {"id": "v2", "nombre": "Zanahoria", "categoria": "Verduras y hortalizas",
         "energia_kcal": 41, "proteina_g": 0.9, "grasa_total_g": 0.2, "carbohidratos_g": 10},
        {"id": "v3", "nombre": "Espinaca", "categoria": "Verduras y hortalizas",
         "energia_kcal": 23, "proteina_g": 2.9, "grasa_total_g": 0.4, "carbohidratos_g": 3.6},
        {"id": "car1", "nombre": "Pechuga de pollo", "categoria": "Carnes y aves",
         "energia_kcal": 165, "proteina_g": 31, "grasa_total_g": 3.6, "carbohidratos_g": 0},
        {"id": "car2", "nombre": "Carne res", "categoria": "Carnes y aves",
         "energia_kcal": 250, "proteina_g": 26, "grasa_total_g": 15, "carbohidratos_g": 0},
        {"id": "p1", "nombre": "Salmón", "categoria": "Pescados y mariscos",
         "energia_kcal": 208, "proteina_g": 20, "grasa_total_g": 13, "carbohidratos_g": 0},
        {"id": "l1", "nombre": "Leche", "categoria": "Lácteos y derivados",
         "energia_kcal": 61, "proteina_g": 3.2, "grasa_total_g": 3.3, "carbohidratos_g": 5},
        {"id": "l2", "nombre": "Yogur", "categoria": "Lácteos y derivados",
         "energia_kcal": 59, "proteina_g": 3.5, "grasa_total_g": 3.3, "carbohidratos_g": 4.7},
        {"id": "h1", "nombre": "Huevo", "categoria": "Huevos",
         "energia_kcal": 155, "proteina_g": 13, "grasa_total_g": 11, "carbohidratos_g": 1.1},
        {"id": "leg1", "nombre": "Lentejas", "categoria": "Legumbres y derivados",
         "energia_kcal": 116, "proteina_g": 9, "grasa_total_g": 0.4, "carbohidratos_g": 20},
    ]
    for f in foods:
        table.put_item(Item=f)


class TestCalcularTMBHarris:
    """Unit tests for Harris-Benedict TMB calculation."""

    def test_hombre_25_anos_70kg_170cm(self):
        from app.routes.sugerencia import calcular_tmb_harris
        # 66.47 + 13.75*70 + 5.0*170 - 6.76*25 = 66.47 + 962.5 + 850 - 169 = 1709.97
        tmb = calcular_tmb_harris(70, 1.70, 25, "Masculino")
        assert 1700 < tmb < 1720

    def test_mujer_30_anos_60kg_160cm(self):
        from app.routes.sugerencia import calcular_tmb_harris
        # 655.10 + 9.56*60 + 1.85*160 - 4.68*30 = 655.10 + 573.6 + 296 - 140.4 = 1384.3
        tmb = calcular_tmb_harris(60, 1.60, 30, "Femenino")
        assert 1380 < tmb < 1390


class TestCalcularDistribucionMacros:
    """Unit tests for macro distribution by profile."""

    def test_normal(self):
        from app.routes.sugerencia import calcular_distribucion_macros
        d = calcular_distribucion_macros("Normal", "Bajo", [])
        assert d["porcentaje_carbohidratos"] == 50
        assert d["porcentaje_proteina"] == 20
        assert d["porcentaje_grasa"] == 30

    def test_sobrepeso(self):
        from app.routes.sugerencia import calcular_distribucion_macros
        d = calcular_distribucion_macros("Sobrepeso", "Bajo", [])
        assert d["porcentaje_proteina"] == 25

    def test_riesgo_cardiovascular_alto(self):
        from app.routes.sugerencia import calcular_distribucion_macros
        d = calcular_distribucion_macros("Normal", "Alto", [])
        assert d["porcentaje_grasa"] == 25

    def test_diabetes(self):
        from app.routes.sugerencia import calcular_distribucion_macros
        d = calcular_distribucion_macros("Normal", "Bajo", ["Diabetes tipo 2"])
        assert d["porcentaje_grasa"] == 35
        assert d["porcentaje_carbohidratos"] == 45

    def test_hipertension(self):
        from app.routes.sugerencia import calcular_distribucion_macros
        d = calcular_distribucion_macros("Normal", "Bajo", ["Hipertensión arterial"])
        assert d.get("restriccion_sodio") is True


class TestGenerarSugerencia:
    """POST /sugerencia/generar"""

    URL = "/sugerencia/generar"

    def test_generar_sugerencia_unauthorized(self, client):
        resp = client.post(self.URL, json={"paciente_id": "pac-001"})
        assert resp.status_code == 401

    def test_generar_sugerencia_basica(self, client, auth_header_teacher):
        resp = client.post(self.URL, json={
            "paciente_id": "pac-001",
            "peso_kg": 70,
            "estatura_m": 1.70,
            "edad": 25,
            "sexo_biologico": "Masculino",
            "factor_actividad": 1.55,
            "imc_clasificacion": "Normal",
            "icc_riesgo": "Bajo",
            "antecedentes": [],
        }, headers=auth_header_teacher)
        assert resp.status_code == 200
        data = resp.json()
        assert "sugerencia_id" in data
        assert data["objetivo_kcal"] > 0
        assert "distribucion_macros" in data
        assert data["distribucion_macros"]["porcentaje_carbohidratos"] == 50
        assert data["formula_utilizada"] == "Harris-Benedict revisada"

    def test_generar_sugerencia_sobrepeso(self, client, auth_header_teacher):
        resp = client.post(self.URL, json={
            "paciente_id": "pac-002",
            "peso_kg": 90,
            "estatura_m": 1.70,
            "edad": 35,
            "sexo_biologico": "Femenino",
            "factor_actividad": 1.55,
            "imc_clasificacion": "Sobrepeso",
            "icc_riesgo": "Bajo",
            "antecedentes": [],
        }, headers=auth_header_teacher)
        assert resp.status_code == 200
        data = resp.json()
        assert data["distribucion_macros"]["porcentaje_proteina"] == 25

    def test_generar_sugerencia_con_alimentos(self, client, auth_header_student):
        from tests.conftest import _get_fake_table
        table = _get_fake_table("alimentos")
        _seed_alimentos_bulk(table)
        resp = client.post(self.URL, json={
            "paciente_id": "pac-003",
            "peso_kg": 70,
            "estatura_m": 1.70,
            "edad": 25,
            "sexo_biologico": "Masculino",
        }, headers=auth_header_student)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["alimentos_sugeridos"]) > 0


class TestAceptarSugerencia:
    """POST /sugerencia/{sugerencia_id}/aceptar"""

    def test_aceptar_sugerencia_exitosa(self, client, auth_header_teacher):
        from tests.conftest import _get_fake_table
        table = _get_fake_table("alimentos")
        _seed_alimentos_bulk(table)

        gen_resp = client.post("/sugerencia/generar", json={
            "paciente_id": "pac-aceptar",
            "peso_kg": 70,
            "estatura_m": 1.70,
            "edad": 25,
            "sexo_biologico": "Masculino",
        }, headers=auth_header_teacher)
        sugerencia_id = gen_resp.json()["sugerencia_id"]

        resp = client.post(f"/sugerencia/{sugerencia_id}/aceptar",
                           headers=auth_header_teacher)
        assert resp.status_code == 200
        data = resp.json()
        assert "plan_id" in data
        assert "eliminado" not in data.get("mensaje", "") or "creado" in data["mensaje"]

    def test_aceptar_sugerencia_no_encontrada(self, client, auth_header_teacher):
        resp = client.post(f"/sugerencia/{uuid.uuid4()}/aceptar",
                           headers=auth_header_teacher)
        assert resp.status_code == 404


class TestHistorialSugerencias:
    """GET /sugerencia/historial/{paciente_id}"""

    def test_historial_vacio(self, client, auth_header_teacher):
        resp = client.get(f"/sugerencia/historial/pac-sin-historial",
                          headers=auth_header_teacher)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0

    def test_historial_con_sugerencias(self, client, auth_header_teacher):
        from tests.conftest import _get_fake_table
        table = _get_fake_table("alimentos")
        _seed_alimentos_bulk(table)
        client.post("/sugerencia/generar", json={
            "paciente_id": "pac-hist",
            "peso_kg": 70, "estatura_m": 1.70, "edad": 25,
            "sexo_biologico": "Masculino",
        }, headers=auth_header_teacher)
        resp = client.get("/sugerencia/historial/pac-hist",
                          headers=auth_header_teacher)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
