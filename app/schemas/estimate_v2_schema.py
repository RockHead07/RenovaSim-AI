# ---------------------------------------------------------------------------
# estimate_v2_schema.py
# Request/response schemas for the v2 estimation endpoint.
# ---------------------------------------------------------------------------

from pydantic import BaseModel, Field
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
    total_range: TotalRangeSchema
    breakdown: list[BreakdownItemSchema]
    assumptions: list[AssumptionItemSchema]
    explanation: list[str]
    warnings: list[WarningSchema]
    conflicts_resolved: list[dict]
    clarification_needed: str | None
    disclaimer: str