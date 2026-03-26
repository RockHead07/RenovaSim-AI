# ---------------------------------------------------------------------------
# models/job_type.py
# Database table definition using SQLModel.
# One class = DB table + Pydantic validation.
# ---------------------------------------------------------------------------

from sqlmodel import SQLModel, Field


class JobType(SQLModel, table=True):
    __tablename__ = "job_types"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    material_price: float = Field(gt=0)
    labor_price: float = Field(gt=0)