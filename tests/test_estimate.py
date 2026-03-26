# ---------------------------------------------------------------------------
# test_estimate.py
# Tests for POST /api/estimate
# ---------------------------------------------------------------------------

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Happy path — valid requests
# ---------------------------------------------------------------------------

class TestValidEstimates:

    def test_painting_50m2(self, client: TestClient):
        response = client.post("/api/estimate", json={"job_type": "painting", "area": 50})
        assert response.status_code == 200
        data = response.json()
        assert data["job_type"] == "painting"
        assert data["area"] == 50
        assert data["material_cost"] == 1_250_000
        assert data["labor_cost"] == 750_000
        assert data["total_cost"] == 2_000_000

    def test_ceramic_30m2(self, client: TestClient):
        response = client.post("/api/estimate", json={"job_type": "ceramic", "area": 30})
        assert response.status_code == 200
        data = response.json()
        assert data["material_cost"] == 3_600_000
        assert data["labor_cost"] == 2_400_000
        assert data["total_cost"] == 6_000_000

    def test_roof_100m2(self, client: TestClient):
        response = client.post("/api/estimate", json={"job_type": "roof", "area": 100})
        assert response.status_code == 200
        data = response.json()
        assert data["material_cost"] == 15_000_000
        assert data["labor_cost"] == 10_000_000
        assert data["total_cost"] == 25_000_000

    def test_job_type_is_case_insensitive(self, client: TestClient):
        """Schema normalises to lowercase — PAINTING should work."""
        response = client.post("/api/estimate", json={"job_type": "PAINTING", "area": 10})
        assert response.status_code == 200
        assert response.json()["job_type"] == "painting"

    def test_fractional_area(self, client: TestClient):
        """Area can be a float."""
        response = client.post("/api/estimate", json={"job_type": "painting", "area": 12.5})
        assert response.status_code == 200
        assert response.json()["material_cost"] == 312_500
        assert response.json()["total_cost"] == 500_000

    def test_response_contains_all_fields(self, client: TestClient):
        """Response must always include every expected field."""
        response = client.post("/api/estimate", json={"job_type": "roof", "area": 20})
        assert response.status_code == 200
        keys = response.json().keys()
        for field in ["job_type", "area", "material_cost", "labor_cost", "total_cost"]:
            assert field in keys


# ---------------------------------------------------------------------------
# Sad path — invalid requests (expect 422)
# ---------------------------------------------------------------------------

class TestInvalidEstimates:

    def test_unsupported_job_type(self, client: TestClient):
        response = client.post("/api/estimate", json={"job_type": "swimming_pool", "area": 50})
        assert response.status_code == 422
        body = response.json()
        assert body["success"] is False
        assert "details" in body

    def test_zero_area(self, client: TestClient):
        response = client.post("/api/estimate", json={"job_type": "painting", "area": 0})
        assert response.status_code == 422

    def test_negative_area(self, client: TestClient):
        response = client.post("/api/estimate", json={"job_type": "painting", "area": -10})
        assert response.status_code == 422

    def test_missing_job_type(self, client: TestClient):
        response = client.post("/api/estimate", json={"area": 50})
        assert response.status_code == 422

    def test_missing_area(self, client: TestClient):
        response = client.post("/api/estimate", json={"job_type": "painting"})
        assert response.status_code == 422

    def test_empty_body(self, client: TestClient):
        response = client.post("/api/estimate", json={})
        assert response.status_code == 422

    def test_wrong_type_for_area(self, client: TestClient):
        """Area must be a number, not a string."""
        response = client.post("/api/estimate", json={"job_type": "painting", "area": "big"})
        assert response.status_code == 422