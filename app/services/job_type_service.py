# ---------------------------------------------------------------------------
# services/job_type_service.py
# Business logic for job type CRUD — no HTTP concerns here.
# ---------------------------------------------------------------------------

import logging
from sqlmodel import Session, select
from app.models.job_type import JobType
from app.schemas.job_type_schema import JobTypeCreate, JobTypeUpdate

logger = logging.getLogger(__name__)


def get_all_job_types(session: Session) -> list[JobType]:
    return list(session.exec(select(JobType)).all())


def get_job_type_by_name(name: str, session: Session) -> JobType | None:
    return session.exec(
        select(JobType).where(JobType.name == name.strip().lower())
    ).first()


def create_job_type(data: JobTypeCreate, session: Session) -> JobType:
    normalised_name = data.name.strip().lower()

    if get_job_type_by_name(normalised_name, session):
        raise ValueError(f"Job type '{normalised_name}' already exists.")

    job_type = JobType(
        name=normalised_name,
        material_price=data.material_price,
        labor_price=data.labor_price,
    )
    session.add(job_type)
    session.commit()
    session.refresh(job_type)
    logger.info(f"Created job type: {normalised_name}")
    return job_type


def update_job_type(name: str, data: JobTypeUpdate, session: Session) -> JobType:
    job_type = get_job_type_by_name(name, session)
    if not job_type:
        raise LookupError(f"Job type '{name}' not found.")

    job_type.material_price = data.material_price
    job_type.labor_price = data.labor_price
    session.commit()
    session.refresh(job_type)
    logger.info(f"Updated job type: {name}")
    return job_type


def delete_job_type(name: str, session: Session) -> None:
    job_type = get_job_type_by_name(name, session)
    if not job_type:
        raise LookupError(f"Job type '{name}' not found.")

    session.delete(job_type)
    session.commit()
    logger.info(f"Deleted job type: {name}")