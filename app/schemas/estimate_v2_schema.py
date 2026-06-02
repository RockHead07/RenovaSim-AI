# ---------------------------------------------------------------------------
# estimate_v2_schema.py
# Request/response schemas for the v2 estimation endpoint.
# ---------------------------------------------------------------------------

from pydantic import BaseModel, Field, model_validator
from typing import Literal


class EstimateV2Request(BaseModel):
    """Full input payload for v2 estimate."""

    project_name: str = Field(default="Proyek Renovasi", description="Nama project")
    location: str | None = Field(default=None, description="Kota/kabupaten lokasi proyek")
    job_type: str | None = Field(default=None, description="Tipe pekerjaan utama")
    quality: Literal["ekonomi", "standar", "premium"] | None = Field(
        default=None, description="Kualitas material"
    )
    scope: Literal["light", "medium", "full"] | None = Field(
        default=None, description="Scope renovasi: ringan/sedang/total"
    )
    area: float | None = Field(default=None, gt=0, description="Luas area dalam m²")
    description: str | None = Field(default=None, description="Deskripsi bebas renovasi")
    budget: float | None = Field(default=None, gt=0, description="Budget user (opsional, untuk sanity check)")


class ConfidenceSchema(BaseModel):
    score: float
    label: str
    message: str


class TotalRangeSchema(BaseModel):
    min: float
    max: float
    display: str


class BreakdownItemSchema(BaseModel):
    job_type: str
    area: float
    min: float
    max: float


class AssumptionItemSchema(BaseModel):
    field: str
    value: object
    source: str
    confidence: float
    impact: str
    reason: str
    needs_clarification: bool
    editable: bool


class WarningSchema(BaseModel):
    type: str
    severity: str
    message: str


class EstimateV2Response(BaseModel):
    """Full output from v2 estimate endpoint."""

    project_name: str
    mode: str
    confidence: ConfidenceSchema
    pre_framing: str
    quality: str | None = None
    location: str | None = None
    total_range: TotalRangeSchema
    breakdown: list[BreakdownItemSchema]
    assumptions: list[AssumptionItemSchema]
    explanation: list[str]
    warnings: list[WarningSchema]
    conflicts_resolved: list[dict]
    clarification_needed: str | None
    disclaimer: str


class RefineRequest(BaseModel):
    """Request to refine a previous estimate with user corrections."""
    previous_result: dict = Field(..., description="The full previous estimate response")
    corrections: dict = Field(
        ...,
        description="Fields to correct: area, quality, location, scope, job_type, budget",
        examples=[{"area": 18, "quality": "premium"}],
    )


class RefineResponse(EstimateV2Response):
    """Refine response — same as v2 but with a refinement note."""
    refinement_note: str


class EstimateAIRequest(BaseModel):
    """Request for AI-powered free-text estimation."""
    project_name: str = Field(default="Proyek Renovasi", description="Nama project")
    text: str | None = Field(
        default=None,
        description="Deskripsi renovasi dalam bahasa bebas",
        examples=["mau cat ruang tamu 4x5 pakai cat bagus di jakarta"],
    )
    description: str | None = Field(
        default=None,
        description="Alias untuk 'text' — diterima untuk kompatibilitas Laravel",
    )
    budget: float | None = Field(default=None, gt=0, description="Budget opsional untuk sanity check")
    area_hint: float | None = Field(default=None, gt=0, description="Optional area hint from session / previous estimation")

    @model_validator(mode="after")
    def resolve_text_field(self) -> "EstimateAIRequest":
        if not self.text and self.description:
            self.text = self.description
        if not self.text or len(self.text.strip()) < 3:
            raise ValueError("Field 'text' atau 'description' wajib diisi (minimal 3 karakter)")
        return self


class EstimateAIResponse(EstimateV2Response):
    """AI estimate response — same as v2 with LLM metadata."""
    llm_used: bool
    llm_extracted: dict | None