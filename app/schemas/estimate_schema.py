# ---------------------------------------------------------------------------
# estimate_schema.py
# Pydantic models for request validation and response serialisation.
# ---------------------------------------------------------------------------

from pydantic import BaseModel, Field, field_validator
from app.data.cost_data import SUPPORTED_JOB_TYPES


class EstimateRequest(BaseModel):
    """Incoming payload for a renovation cost estimate."""

    job_type: str = Field(
        ...,
        description=f"Type of renovation job. Supported: {SUPPORTED_JOB_TYPES}",
        examples=["painting"],
    )
    area: float = Field(
        ...,
        gt=0,
        description="Area in square metres (must be greater than 0)",
        examples=[50.0],
    )

    @field_validator("job_type")
    @classmethod
    def job_type_must_be_supported(cls, value: str) -> str:
        normalised = value.strip().lower()
        if normalised not in SUPPORTED_JOB_TYPES:
            raise ValueError(
                f"'{value}' is not a supported job type. "
                f"Choose from: {SUPPORTED_JOB_TYPES}"
            )
        return normalised


class EstimateResponse(BaseModel):
    """Structured cost breakdown returned by the API."""

    job_type: str
    area: float
    material_cost: float
    labor_cost: float
    total_cost: float
