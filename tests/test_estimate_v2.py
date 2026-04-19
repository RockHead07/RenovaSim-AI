# ---------------------------------------------------------------------------
# test_estimate_v2.py
# Tests for POST /api/v2/estimate and PATCH /api/v2/estimate/refine
# ---------------------------------------------------------------------------

import pytest
from fastapi.testclient import TestClient


class TestEstimateV2FullInput:
    """Happy path — complete input from wizard."""

    def test_full_input_painting_jakarta(self, client: TestClient):
        response = client.post("/api/v2/estimate", json={
            "project_name": "Test Painting",
            "location": "jakarta",
            "job_type": "painting",
            "quality": "standar",
            "scope": "medium",
            "area": 50,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["mode"] == "standard"
        assert data["confidence"]["score"] >= 0.75
        assert data["total_range"]["min"] > 0
        assert data["total_range"]["max"] > data["total_range"]["min"]
        assert len(data["breakdown"]) > 0
        assert data["pre_framing"] != ""
        assert data["disclaimer"] != ""

    def test_full_input_ceramic_bandung(self, client: TestClient):
        response = client.post("/api/v2/estimate", json={
            "project_name": "Test Ceramic",
            "location": "bandung",
            "job_type": "ceramic",
            "quality": "premium",
            "scope": "medium",
            "area": 20,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["mode"] == "standard"
        assert data["total_range"]["min"] > 0

    def test_response_has_all_required_fields(self, client: TestClient):
        response = client.post("/api/v2/estimate", json={
            "job_type": "painting",
            "area": 30,
        })
        assert response.status_code == 200
        data = response.json()
        for field in [
            "mode", "confidence", "pre_framing", "total_range",
            "breakdown", "assumptions", "explanation",
            "warnings", "disclaimer"
        ]:
            assert field in data, f"Missing field: {field}"

    def test_explanation_is_human_readable(self, client: TestClient):
        response = client.post("/api/v2/estimate", json={
            "location": "jakarta",
            "job_type": "ceramic",
            "quality": "standar",
            "area": 20,
        })
        assert response.status_code == 200
        data = response.json()
        assert len(data["explanation"]) > 0
        for line in data["explanation"]:
            assert isinstance(line, str)
            assert len(line) > 10


class TestEstimateV2VagueInput:
    """Vague input — system should use assumptions."""

    def test_vague_kamar_mandi(self, client: TestClient):
        response = client.post("/api/v2/estimate", json={
            "description": "mau renovasi kamar mandi kecil",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["mode"] in ["best_effort", "standard"]
        assert data["confidence"]["score"] <= 0.50
        assert data["clarification_needed"] is not None

    def test_vague_no_input(self, client: TestClient):
        response = client.post("/api/v2/estimate", json={
            "project_name": "Empty Project",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["mode"] in ["best_effort", "incomplete"]

    def test_description_with_dimensions(self, client: TestClient):
        response = client.post("/api/v2/estimate", json={
            "description": "mau ngecat ruang tamu 4x5 meter",
            "location": "jakarta",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["total_range"]["min"] > 0


class TestEstimateV2RoomBundle:
    """Room bundle — room name should expand to multiple jobs."""

    def test_bathroom_medium_scope(self, client: TestClient):
        response = client.post("/api/v2/estimate", json={
            "description": "renovasi kamar mandi",
            "area": 6,
            "quality": "standar",
            "scope": "medium",
            "location": "jakarta",
        })
        assert response.status_code == 200
        data = response.json()
        job_types = [b["job_type"] for b in data["breakdown"]]
        assert "plumbing" in job_types
        assert "ceramic" in job_types

    def test_kitchen_full_scope(self, client: TestClient):
        response = client.post("/api/v2/estimate", json={
            "description": "renovasi total dapur",
            "area": 12,
            "quality": "standar",
            "location": "bandung",
        })
        assert response.status_code == 200
        data = response.json()
        assert len(data["breakdown"]) >= 2


class TestEstimateV2Warnings:
    """Sanity check warnings."""

    def test_underbudget_warning(self, client: TestClient):
        response = client.post("/api/v2/estimate", json={
            "job_type": "ceramic",
            "quality": "premium",
            "area": 50,
            "location": "jakarta",
            "budget": 500_000,
        })
        assert response.status_code == 200
        data = response.json()
        warning_types = [w["type"] for w in data["warnings"]]
        assert "underbudget" in warning_types

    def test_no_warning_for_adequate_budget(self, client: TestClient):
        response = client.post("/api/v2/estimate", json={
            "job_type": "painting",
            "quality": "ekonomi",
            "area": 10,
            "location": "jogja",
            "budget": 50_000_000,
        })
        assert response.status_code == 200
        data = response.json()
        warning_types = [w["type"] for w in data["warnings"]]
        assert "underbudget" not in warning_types


class TestEstimateV2Confidence:
    """Confidence system."""

    def test_full_input_gives_high_confidence(self, client: TestClient):
        response = client.post("/api/v2/estimate", json={
            "location": "jakarta",
            "job_type": "painting",
            "quality": "standar",
            "area": 50,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["confidence"]["score"] >= 0.75
        assert data["confidence"]["label"] in ["Tinggi", "Sedang"]

    def test_missing_area_caps_confidence(self, client: TestClient):
        response = client.post("/api/v2/estimate", json={
            "job_type": "painting",
            "quality": "standar",
            "location": "jakarta",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["confidence"]["score"] <= 0.50

    def test_low_confidence_for_vague_input(self, client: TestClient):
        low = client.post("/api/v2/estimate", json={
            "description": "mau renov rumah",
        }).json()

        high = client.post("/api/v2/estimate", json={
            "job_type": "painting",
            "quality": "standar",
            "area": 30,
            "location": "jakarta",
        }).json()

        assert high["confidence"]["score"] > low["confidence"]["score"]


class TestEstimateV2Refine:
    """Refine endpoint — update assumptions in-place."""

    def _get_initial_estimate(self, client: TestClient) -> dict:
        response = client.post("/api/v2/estimate", json={
            "project_name": "Renovasi Test",
            "description": "mau renovasi kamar mandi kecil",
            "location": "jakarta",
        })
        return response.json()

    def test_refine_returns_200(self, client: TestClient):
        initial = self._get_initial_estimate(client)
        response = client.patch("/api/v2/estimate/refine", json={
            "previous_result": initial,
            "corrections": {"area": 18, "quality": "standar"},
        })
        assert response.status_code == 200

    def test_refine_has_refinement_note(self, client: TestClient):
        initial = self._get_initial_estimate(client)
        response = client.patch("/api/v2/estimate/refine", json={
            "previous_result": initial,
            "corrections": {"area": 18},
        })
        assert response.status_code == 200
        data = response.json()
        assert "refinement_note" in data
        assert "area" in data["refinement_note"]

    def test_refine_has_valid_range(self, client: TestClient):
        initial = self._get_initial_estimate(client)
        response = client.patch("/api/v2/estimate/refine", json={
            "previous_result": initial,
            "corrections": {"area": 18, "quality": "standar"},
        })
        assert response.status_code == 200
        data = response.json()
        assert data["total_range"]["min"] > 0
        assert data["total_range"]["max"] >= data["total_range"]["min"]

    def test_refine_confidence_improves_with_more_info(self, client: TestClient):
        initial = self._get_initial_estimate(client)
        initial_confidence = initial["confidence"]["score"]

        refined = client.patch("/api/v2/estimate/refine", json={
            "previous_result": initial,
            "corrections": {"area": 9, "quality": "standar", "job_type": "ceramic"},
        }).json()

        assert refined["confidence"]["score"] >= initial_confidence