"""
Tests for the food catalog routes (RF9, RF12, RNF14, RES2).
Uses mock DynamoDB from conftest.
"""


class TestListarAlimentos:
    """GET /alimentos"""

    URL = "/alimentos"

    def _seed_alimento(self, client, alimento_id="alim-001", nombre="Arroz blanco",
                       categoria="Cereales y derivados"):
        from tests.conftest import _get_fake_table
        table = _get_fake_table("alimentos")
        table.put_item(Item={
            "id": alimento_id,
            "nombre": nombre,
            "nombre_ingles": f"{nombre} english",
            "categoria": categoria,
            "energia_kcal": 130,
            "proteina_g": 2.7,
            "grasa_total_g": 0.3,
            "carbohidratos_g": 28.2,
        })

    def test_listar_alimentos_unauthorized(self, client):
        resp = client.get(self.URL)
        assert resp.status_code == 401

    def test_listar_alimentos_empty(self, client, auth_header_teacher):
        resp = client.get(self.URL, headers=auth_header_teacher)
        assert resp.status_code == 200
        data = resp.json()
        assert data["alimentos"] == []
        assert data["total"] == 0

    def test_listar_alimentos_con_datos(self, client, auth_header_teacher):
        self._seed_alimento(client)
        resp = client.get(self.URL, headers=auth_header_teacher)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["alimentos"][0]["nombre"] == "Arroz blanco"
        assert data["alimentos"][0]["energia_kcal"] == 130

    def test_buscar_por_nombre(self, client, auth_header_teacher):
        self._seed_alimento(client, alimento_id="a1", nombre="Arroz blanco")
        self._seed_alimento(client, alimento_id="a2", nombre="Pollo a la brasa",
                           categoria="Carnes y aves")
        resp = client.get(f"{self.URL}?buscar=arroz", headers=auth_header_teacher)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["alimentos"][0]["nombre"] == "Arroz blanco"

    def test_filtrar_por_categoria(self, client, auth_header_teacher):
        self._seed_alimento(client, alimento_id="a1", nombre="Arroz",
                           categoria="Cereales y derivados")
        self._seed_alimento(client, alimento_id="a2", nombre="Manzana",
                           categoria="Frutas")
        resp = client.get(f"{self.URL}?categoria=Frutas", headers=auth_header_teacher)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["alimentos"][0]["nombre"] == "Manzana"

    def test_paginacion(self, client, auth_header_teacher):
        for i in range(5):
            self._seed_alimento(client, alimento_id=f"a{i}", nombre=f"Alimento {i}")
        resp = client.get(f"{self.URL}?limite=2&offset=0", headers=auth_header_teacher)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 5
        assert len(data["alimentos"]) == 2
        assert data["limite"] == 2
        assert data["offset"] == 0


class TestListarCategorias:
    """GET /alimentos/categorias"""

    URL = "/alimentos/categorias"

    def _seed_multiple(self, client):
        from tests.conftest import _get_fake_table
        table = _get_fake_table("alimentos")
        for i, cat in enumerate(["Frutas", "Verduras", "Frutas"]):
            table.put_item(Item={"id": f"alim-{i}", "nombre": f"Alimento {i}",
                                 "categoria": cat, "energia_kcal": 100})

    def test_categorias_vacio(self, client, auth_header_teacher):
        resp = client.get(self.URL, headers=auth_header_teacher)
        assert resp.status_code == 200
        assert resp.json()["categorias"] == []

    def test_categorias_con_datos(self, client, auth_header_teacher):
        self._seed_multiple(client)
        resp = client.get(self.URL, headers=auth_header_teacher)
        assert resp.status_code == 200
        cats = resp.json()["categorias"]
        assert "Frutas" in cats
        assert "Verduras" in cats
        assert len(cats) == 2


class TestObtenerAlimento:
    """GET /alimentos/{alimento_id}"""

    URL = "/alimentos/alim-001"

    def _seed(self, client):
        from tests.conftest import _get_fake_table
        table = _get_fake_table("alimentos")
        table.put_item(Item={
            "id": "alim-001", "nombre": "Plátano",
            "categoria": "Frutas", "energia_kcal": 93,
        })

    def test_obtener_alimento_no_encontrado(self, client, auth_header_teacher):
        resp = client.get("/alimentos/no-existe", headers=auth_header_teacher)
        assert resp.status_code == 404

    def test_obtener_alimento_exitoso(self, client, auth_header_teacher):
        self._seed(client)
        resp = client.get(self.URL, headers=auth_header_teacher)
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "alim-001"
        assert data["nombre"] == "Plátano"
        assert data["energia_kcal"] == 93

    def test_obtener_alimento_unauthorized(self, client):
        resp = client.get(self.URL)
        assert resp.status_code == 401
