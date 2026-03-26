# ---------------------------------------------------------------------------
# api/job_types.py
# CRUD routes for managing job types — thin layer, no business logic.
# ---------------------------------------------------------------------------

import logging
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session
from app.schemas.job_type_schema import JobTypeCreate, JobTypeUpdate, JobTypeResponse
from app.services.job_type_service import (
    get_all_job_types,
    create_job_type,
    update_job_type,
    delete_job_type,
)
from app.db.session import get_session

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/job-types", tags=["Job Types"])


@router.get("", response_model=list[JobTypeResponse], summary="List all job types")
def list_job_types(session: Session = Depends(get_session)):
    return get_all_job_types(session)


@router.post("", response_model=JobTypeResponse, status_code=201, summary="Add a new job type")
def add_job_type(data: JobTypeCreate, session: Session = Depends(get_session)):
    try:
        return create_job_type(data, session)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.put("/{name}", response_model=JobTypeResponse, summary="Update prices for a job type")
def edit_job_type(name: str, data: JobTypeUpdate, session: Session = Depends(get_session)):
    try:
        return update_job_type(name, data, session)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{name}", status_code=204, summary="Delete a job type")
def remove_job_type(name: str, session: Session = Depends(get_session)):
    try:
        delete_job_type(name, session)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))