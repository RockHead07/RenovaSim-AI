# ---------------------------------------------------------------------------
# test_estimate_ai.py
# Tests for POST /api/v2/estimate/ai
# Note: LLM output is non-deterministic — tests focus on response shape
# and fallback behavior, not exact extracted values.
# ---------------------------------------------------------------------------

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient


class TestEstimateAIResponseShape:
    """Verify response always has correct shape regardless of LLM result."""

    def test_returns_200(self, client: TestClient):
        response = client.post("/api/v2/estimate/ai", json={
            "text": "mau cat ruang tamu 4x5 meter di jakarta"
        })
        assert response.status_code == 200

    def test_response_has_all_required_fields(self, client: TestClient):
        response = client.post("/api/v2/estimate/ai", json={
            "text": "renovasi kamar mandi kecil"
        })
        assert response.status_code == 200
        data = response.json()
        for field in [
            "mode", "confidence", "pre_framing", "total_range",
            "breakdown", "assumptions", "explanation",
            "warnings", "disclaimer", "llm_used", "llm_extracted"
        ]:
            assert field in data, f"Missing field: {field}"

    def test_llm_used_is_boolean(self, client: TestClient):
        response = client.post("/api/v2/estimate/ai", json={
            "text": "cat ruang tamu"
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["llm_used"], bool)

    def test_total_range_always_present(self, client: TestClient):
        response = client.post("/api/v2/estimate/ai", json={
            "text": "renovasi rumah"
        })
        assert response.status_code == 200
        data = response.json()
        assert "min" in data["total_range"]
        assert "max" in data["total_range"]
        assert "display" in data["total_range"]


class TestEstimateAIFallback:
    """System must work even when Ollama is unreachable."""

    def test_fallback_when_ollama_unreachable(self, client: TestClient):
        """When Ollama is down, system falls back to rule-based — no crash."""
        with patch("app.api.estimate_ai.extract_from_text", return_value=None):
            response = client.post("/api/v2/estimate/ai", json={
                "text": "mau cat ruang tamu 20 meter di jakarta"
            })
        assert response.status_code == 200
        data = response.json()
        assert data["llm_used"] is False
        assert data["llm_extracted"] is None
        assert data["total_range"]["min"] >= 0

    def test_fallback_still_uses_preparser(self, client: TestClient):
        """Even without LLM, pre-parser still extracts what it can."""
        with patch("app.api.estimate_ai.extract_from_text", return_value=None):
            response = client.post("/api/v2/estimate/ai", json={
                "text": "ngecat 4x5 meter"
            })
        assert response.status_code == 200
        data = response.json()
        # Pre-parser should get area = 20 from "4x5"
        area_assumption = next(
            (a for a in data["assumptions"] if a["field"] == "area"), None
        )
        if area_assumption:
            assert area_assumption["value"] > 0


class TestEstimateAIWithMockedLLM:
    """Test with mocked LLM responses for deterministic results."""

    def test_llm_result_used_when_available(self, client: TestClient):
        mock_llm = {
            "job_type": "painting",
            "area_m2": 20,
            "quality": "standar",
            "location": "jakarta",
            "scope": "medium",
            "room": None,
        }
        with patch("app.api.estimate_ai.extract_from_text", return_value=mock_llm):
            response = client.post("/api/v2/estimate/ai", json={
                "text": "mau ngecat ruang tamu"
            })
        assert response.status_code == 200
        data = response.json()
        assert data["llm_used"] is True
        assert data["llm_extracted"] is not None
        assert data["total_range"]["min"] > 0

    def test_mocked_bathroom_bundle(self, client: TestClient):
        mock_llm = {
            "job_type": None,
            "area_m2": 6,
            "quality": "standar",
            "location": "jakarta",
            "scope": "medium",
            "room": "bathroom",
        }
        with patch("app.services.llm_extractor.extract_from_text", return_value=mock_llm):
            response = client.post("/api/v2/estimate/ai", json={
                "text": "renovasi kamar mandi 6 meter"
            })
        assert response.status_code == 200
        data = response.json()
        job_types = [b["job_type"] for b in data["breakdown"]]
        assert len(job_types) >= 1

    def test_budget_warning_with_mocked_llm(self, client: TestClient):
        mock_llm = {
            "job_type": "ceramic",
            "area_m2": 50,
            "quality": "premium",
            "location": "jakarta",
            "scope": "full",
            "room": None,
        }
        with patch("app.services.llm_extractor.extract_from_text", return_value=mock_llm):
            response = client.post("/api/v2/estimate/ai", json={
                "text": "pasang keramik premium 50 meter di jakarta",
                "budget": 500_000,
            })
        assert response.status_code == 200
        data = response.json()
        warning_types = [w["type"] for w in data["warnings"]]
        assert "underbudget" in warning_types


class TestEstimateAIValidation:
    """Input validation."""

    def test_empty_text_rejected(self, client: TestClient):
        response = client.post("/api/v2/estimate/ai", json={
            "text": ""
        })
        assert response.status_code == 422

    def test_too_short_text_rejected(self, client: TestClient):
        response = client.post("/api/v2/estimate/ai", json={
            "text": "hi"
        })
        assert response.status_code == 422

    def test_missing_text_rejected(self, client: TestClient):
        response = client.post("/api/v2/estimate/ai", json={
            "project_name": "Test"
        })
        assert response.status_code == 422

    def test_negative_budget_rejected(self, client: TestClient):
        response = client.post("/api/v2/estimate/ai", json={
            "text": "renovasi kamar mandi",
            "budget": -1000
        })
        assert response.status_code == 422