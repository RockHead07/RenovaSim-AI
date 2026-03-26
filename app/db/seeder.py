# ---------------------------------------------------------------------------
# db/seeder.py
# Pre-fills the database with default job types on first run.
# Safe to call multiple times — skips existing entries.
# ---------------------------------------------------------------------------

import logging
from sqlmodel import Session, select
from app.models.job_type import JobType
from app.data.cost_data import COST_TABLE

logger = logging.getLogger(__name__)


def seed_job_types(session: Session) -> None:
    """Insert default job types from cost_data.py if they don't exist."""
    for name, prices in COST_TABLE.items():
        exists = session.exec(
            select(JobType).where(JobType.name == name)
        ).first()

        if not exists:
            job_type = JobType(
                name=name,
                material_price=prices["material"],
                labor_price=prices["labor"],
            )
            session.add(job_type)
            logger.info(f"Seeded job type: {name}")

    session.commit()