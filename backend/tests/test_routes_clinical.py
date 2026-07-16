"""
Tests for the clinical calculation endpoint.

These are PURE logic tests — they verify the anthropometric formulas (IMC, ICC,
TMB, GET) return correct values for known inputs without mocking.
"""

import pytest


class TestClinicalCalculate:
    """Test the /clinical/calculate endpoint."""

    CALC_URL = "/clinical/calculate"

    def _valid_payload(self, **overrides):
        payload = {
            "peso_kg": 70.0,
            "estatura_m": 1.75,
            "perimetro_cintura_cm": 80.0,
            "perimetro_cadera_cm": 95.0,
            "sexo_biologico": "Masculino",
            "edad": 30,
            "factor_actividad": 1.55,
            "efecto_termogenico": 10.0,
        }
        payload.update(overrides)
        return payload

    # ── IMC Tests ──────────────────────────────────────────────

    def test_imc_normal(self, client, auth_header_student):
        """IMC for 70kg / 1.75m should be 22.86 (Normal)."""
        resp = client.post(self.CALC_URL, json=self._valid_payload(), headers=auth_header_student)
        assert resp.status_code == 200
        data = resp.json()
        assert data["imc"] == 22.86
        assert data["imc_clasificacion"] == "Normal"

    def test_imc_bajo_peso(self, client, auth_header_student):
        """IMC < 18.5 should be classified as 'Bajo peso'."""
        resp = client.post(self.CALC_URL, json=self._valid_payload(peso_kg=50.0), headers=auth_header_student)
        assert resp.status_code == 200
        data = resp.json()
        assert data["imc"] < 18.5
        assert data["imc_clasificacion"] == "Bajo peso"

    def test_imc_sobrepeso(self, client, auth_header_student):
        """IMC between 25 and 30 should be 'Sobrepeso'."""
        resp = client.post(self.CALC_URL, json=self._valid_payload(peso_kg=85.0), headers=auth_header_student)
        assert resp.status_code == 200
        data = resp.json()
        assert 25.0 <= data["imc"] < 30.0
        assert data["imc_clasificacion"] == "Sobrepeso"

    def test_imc_obesidad(self, client, auth_header_student):
        """IMC >= 30 should be 'Obesidad'."""
        resp = client.post(self.CALC_URL, json=self._valid_payload(peso_kg=100.0), headers=auth_header_student)
        assert resp.status_code == 200
        data = resp.json()
        assert data["imc"] >= 30.0
        assert data["imc_clasificacion"] == "Obesidad"

    # ── ICC Tests ──────────────────────────────────────────────

    def test_icc_masculino_bajo(self, client, auth_header_student):
        """ICC <= 0.90 for male should be 'Bajo' risk."""
        resp = client.post(
            self.CALC_URL,
            json=self._valid_payload(perimetro_cintura_cm=80.0, perimetro_cadera_cm=95.0),
            headers=auth_header_student,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["icc"] <= 0.90
        assert data["icc_riesgo"] == "Bajo"
        assert data["distribucion_grasa"] == "Ginecoide (Pera)"

    def test_icc_masculino_moderado(self, client, auth_header_student):
        """ICC between 0.90 and 0.95 for male should be 'Moderado'."""
        resp = client.post(
            self.CALC_URL,
            json=self._valid_payload(perimetro_cintura_cm=90.0, perimetro_cadera_cm=97.0),
            headers=auth_header_student,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert 0.90 < data["icc"] <= 0.95
        assert data["icc_riesgo"] == "Moderado"

    def test_icc_masculino_alto(self, client, auth_header_student):
        """ICC > 0.95 for male should be 'Alto' risk with androide distribution."""
        resp = client.post(
            self.CALC_URL,
            json=self._valid_payload(perimetro_cintura_cm=100.0, perimetro_cadera_cm=95.0),
            headers=auth_header_student,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["icc"] > 0.95
        assert data["icc_riesgo"] == "Alto"
        assert data["distribucion_grasa"] == "Obesidad Androide (Manzana)"

    def test_icc_femenino_bajo(self, client, auth_header_student):
        """ICC <= 0.80 for female should be 'Bajo' risk."""
        resp = client.post(
            self.CALC_URL,
            json=self._valid_payload(sexo_biologico="Femenino", perimetro_cintura_cm=70.0, perimetro_cadera_cm=95.0),
            headers=auth_header_student,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["icc"] <= 0.80
        assert data["icc_riesgo"] == "Bajo"

    def test_icc_femenino_moderado(self, client, auth_header_student):
        """ICC between 0.80 and 0.85 for female should be 'Moderado'."""
        resp = client.post(
            self.CALC_URL,
            json=self._valid_payload(sexo_biologico="Femenino", perimetro_cintura_cm=78.0, perimetro_cadera_cm=93.0),
            headers=auth_header_student,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert 0.80 < data["icc"] <= 0.85
        assert data["icc_riesgo"] == "Moderado"

    def test_icc_femenino_alto(self, client, auth_header_student):
        """ICC > 0.85 for female should be 'Alto' risk."""
        resp = client.post(
            self.CALC_URL,
            json=self._valid_payload(sexo_biologico="Femenino", perimetro_cintura_cm=90.0, perimetro_cadera_cm=95.0),
            headers=auth_header_student,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["icc"] > 0.85
        assert data["icc_riesgo"] == "Alto"

    # ── TMB Tests (Harris-Benedict) ────────────────────────────

    def test_tmb_harris_masculino(self, client, auth_header_student):
        """TMB Harris-Benedict for male: 66.47 + 13.75*70 + 5.0*175 - 6.76*30"""
        resp = client.post(self.CALC_URL, json=self._valid_payload(), headers=auth_header_student)
        data = resp.json()
        expected = round(66.47 + (13.75 * 70) + (5.0 * 175) - (6.76 * 30), 2)
        assert data["tmb_harris"] == expected

    def test_tmb_harris_femenino(self, client, auth_header_student):
        """TMB Harris-Benedict for female: 655.10 + 9.56*60 + 1.85*165 - 4.68*25"""
        resp = client.post(
            self.CALC_URL,
            json=self._valid_payload(sexo_biologico="Femenino", peso_kg=60.0, estatura_m=1.65, edad=25),
            headers=auth_header_student,
        )
        data = resp.json()
        expected = round(655.10 + (9.56 * 60) + (1.85 * 165) - (4.68 * 25), 2)
        assert data["tmb_harris"] == expected

    # ── TMB Tests (Mifflin-St Jeor) ────────────────────────────

    def test_tmb_mifflin_masculino(self, client, auth_header_student):
        """TMB Mifflin for male: (10*70) + (6.25*175) - (5*30) + 5"""
        resp = client.post(self.CALC_URL, json=self._valid_payload(), headers=auth_header_student)
        data = resp.json()
        expected = round((10 * 70) + (6.25 * 175) - (5 * 30) + 5, 2)
        assert data["tmb_mifflin"] == expected

    def test_tmb_mifflin_femenino(self, client, auth_header_student):
        """TMB Mifflin for female: (10*60) + (6.25*165) - (5*25) - 161"""
        resp = client.post(
            self.CALC_URL,
            json=self._valid_payload(sexo_biologico="Femenino", peso_kg=60.0, estatura_m=1.65, edad=25),
            headers=auth_header_student,
        )
        data = resp.json()
        expected = round((10 * 60) + (6.25 * 165) - (5 * 25) - 161, 2)
        assert data["tmb_mifflin"] == expected

    # ── GET Tests ──────────────────────────────────────────────

    def test_gasto_total_harris(self, client, auth_header_student):
        """GET = TMB_harris * factor_actividad * (1 + efecto_termogenico/100)"""
        resp = client.post(self.CALC_URL, json=self._valid_payload(), headers=auth_header_student)
        data = resp.json()
        tmb = data["tmb_harris"]
        expected = round((tmb * 1.55) * (1 + 10 / 100), 2)
        assert data["gasto_total_harris"] == expected

    def test_gasto_total_mifflin(self, client, auth_header_student):
        """GET = TMB_mifflin * factor_actividad * (1 + efecto_termogenico/100)"""
        resp = client.post(self.CALC_URL, json=self._valid_payload(), headers=auth_header_student)
        data = resp.json()
        tmb = data["tmb_mifflin"]
        expected = round((tmb * 1.55) * (1 + 10 / 100), 2)
        assert data["gasto_total_mifflin"] == expected

    # ── Validation & Edge Cases ────────────────────────────────

    def test_invalid_sexo(self, client, auth_header_student):
        """An invalid sexo_biologico value should return 400."""
        resp = client.post(
            self.CALC_URL,
            json=self._valid_payload(sexo_biologico="Otro"),
            headers=auth_header_student,
        )
        assert resp.status_code == 400
        assert "sexo biológico" in resp.json()["detail"].lower()

    def test_negative_weight_raises_422(self, client, auth_header_student):
        """A negative weight should fail Pydantic validation (422)."""
        resp = client.post(
            self.CALC_URL,
            json=self._valid_payload(peso_kg=-10),
            headers=auth_header_student,
        )
        assert resp.status_code == 422

    def test_zero_height_raises_422(self, client, auth_header_student):
        """Zero height should fail Pydantic validation (422)."""
        resp = client.post(
            self.CALC_URL,
            json=self._valid_payload(estatura_m=0),
            headers=auth_header_student,
        )
        assert resp.status_code == 422

    def test_negative_efecto_raises_422(self, client, auth_header_student):
        """Negative efecto_termogenico should fail validation (422)."""
        resp = client.post(
            self.CALC_URL,
            json=self._valid_payload(efecto_termogenico=-1),
            headers=auth_header_student,
        )
        assert resp.status_code == 422

    def test_missing_auth(self, client):
        """Without auth header, should return 401 (Unauthorized)."""
        resp = client.post(self.CALC_URL, json=self._valid_payload())
        assert resp.status_code == 401

    def test_unauthenticated_returns_401(self, client):
        """A request with a garbage token should return 401."""
        resp = client.post(
            self.CALC_URL,
            json=self._valid_payload(),
            headers={"Authorization": "Bearer invalid-token-here"},
        )
        assert resp.status_code == 401
