# ---------------------------------------------------------------------------
# schemas/job_type_schema.py
# Pydantic schemas for job type CRUD requests and responses.
# ---------------------------------------------------------------------------

from pydantic import BaseModel, Field


class JobTypeCreate(BaseModel):
    """Payload for creating a new job type."""
    name: str = Field(..., min_length=1, description="Unique name for the job type")
    material_price: float = Field(..., gt=0, description="Material cost per m²")
    labor_price: float = Field(..., gt=0, description="Labour cost per m²")


class JobTypeUpdate(BaseModel):
    """Payload for updating prices of an existing job type."""
    material_price: float = Field(..., gt=0, description="Material cost per m²")
    labor_price: float = Field(..., gt=0, description="Labour cost per m²")


class JobTypeResponse(BaseModel):
    """Returned job type data."""
    id: int
    name: str
    material_price: float
    labor_price: float

    model_config = {"from_attributes": True}