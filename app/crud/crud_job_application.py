from datetime import datetime

from sqlalchemy import desc, asc, or_, select, and_
from sqlalchemy.orm import Session

from app.core.logging_config import logger
from app.core.util import decode_cursor, encode_cursor, retrieve_last_item_key, cast_to_column_type
from app.models.association import documents_association_table
from app.models.documents import Documents
from app.models.job_application import JobApplication, Interview, \
    JobApplicationStatusTransitionType
from app.models.user import User
from app.schemas import job_application
from app.schemas.job_application import ApiResponse, JobFilterParams, JobApplicationStatusTransition
from app.services.state_machine import job_application_state_machine
from dateutil import parser

SORTABLE_COLUMNS = {
    "created_at": JobApplication.created_at,
    "updated_at": JobApplication.updated_at,
    "company_name": JobApplication.company_name,
    "status": JobApplication.status,
}

def create_job_application(data: job_application.JobApplicationCreate, user: User):
    try:
        job_application_instance = JobApplication(
            company_name=data.company_name,
            job_url=data.job_url,
            job_title=data.job_title,
            description=data.description,
            user_id=user.id,
            notes=data.notes,
            status="saved",
            source=data.source,
        )
        job_application_instance.save_to_db()
        return {
            "success": True,
            "message": "Job application created successfully",
            "data": {
                "id": job_application_instance.id,
                "job_title": job_application_instance.job_title
            }
        }
    except Exception as e:
        logger.error(e)
        raise Exception("Error creating job application")


def get_job_application_by_id(job_id: str, user: User, db: Session):
    try:
        db_job = db.query(JobApplication).filter(JobApplication.id == job_id,
                                                 JobApplication.user_id == user.id).first()
        if not db_job:
            raise Exception("Job application not found")
        docs = (db.query(Documents)
                .join(documents_association_table, documents_association_table.c.documents_id == Documents.id)
                .join(JobApplication, JobApplication.id == documents_association_table.c.job_application_id).all())
        db_job.documents = docs
        interviews = db.query(Interview).filter(Interview.job_application_id == job_id).all()
        db_job.interviews = interviews
        return ApiResponse(success=True, payload=db_job)
    except Exception as error:
        logger.error(error)
        raise Exception("Error getting job application")


def get_job_applications(user: User, db: Session, filters: JobFilterParams, limit: int = 20, cursor: str = None):
    try:
        stmt = select(JobApplication).where(JobApplication.user_id == user.id, JobApplication.is_archived == False)

        sort_column = SORTABLE_COLUMNS.get(filters.sort_by, JobApplication.created_at)

        # Filtering
        if filters.company_name:
            stmt = stmt.where(JobApplication.company_name.ilike(f"%{filters.company_name}%"))
        if filters.status:
            stmt = stmt.where(JobApplication.status == filters.status)
        if filters.start_date:
            stmt = stmt.where(JobApplication.created_at >= filters.start_date)
        if filters.end_date:
            stmt = stmt.where(JobApplication.created_at <= filters.end_date)

        # Searching
        if filters.q:
            stmt = stmt.where(
                or_(
                    JobApplication.company_name.ilike(f"%{filters.q}%"),
                    JobApplication.job_title.ilike(f"%{filters.q}%")
                )
            )

        # 3. Apply Cursor (finding the starting point)
        if cursor:
            raw_val, last_id = decode_cursor(cursor)
            typed_val = cast_to_column_type(raw_val, sort_column)

            if filters.order == "desc":
                stmt = stmt.where(
                    or_(
                        sort_column < typed_val,
                        and_(sort_column == typed_val, JobApplication.id < last_id)
                    )
                )
            else:
                stmt = stmt.where(
                    or_(
                        sort_column > typed_val,
                        and_(sort_column == typed_val, JobApplication.id > last_id)
                    )
                )
        # Sorting
        if filters.order == "desc":
            stmt = stmt.order_by(desc(sort_column), desc(JobApplication.id))
        else:
            stmt = stmt.order_by(asc(sort_column), asc(JobApplication.id))

        stmt = stmt.limit(limit + 1)
        results = db.execute(stmt).scalars().all()
        next_cursor = None
        has_next_page = len(results) > limit
        db_jobs = results[:limit] if results else results

        if has_next_page:
            last_item = db_jobs[-1]
            try:
                last_item_key = retrieve_last_item_key(filters.sort_by, last_item)
                next_cursor = encode_cursor(last_item_key, last_item.id)
            except Exception as e:
                logger.error(e)
                next_cursor = None

        return ApiResponse(success=True, payload={"data": db_jobs, "next_cursor": next_cursor})
    except Exception as error:
        logger.error(error)
        raise Exception("Error getting job applications")


def update_job_application(
        data: job_application.JobApplicationUpdate,
        db: Session,
        job_id: str):
    try:
        db_job_app = db.query(JobApplication).filter(JobApplication.id == job_id).first()
        if db_job_app is None:
            raise Exception("Job application not found")
        db_job_app.notes = data.notes if data.notes else db_job_app.notes
        db_job_app.updated_at = datetime.now()
        db_job_app.company_name = data.company_name if data.company_name else db_job_app.company_name
        db_job_app.job_url = data.job_url if data.job_url else db_job_app.job_url
        db_job_app.job_title = data.job_title if data.job_title else db_job_app.job_title
        db_job_app.description = data.description if data.description else db_job_app.description
        db_job_app.source = data.source if data.source else db_job_app.source
        db_job_app.date_applied = parser.parse(data.date_applied) if data.date_applied else db_job_app.date_applied
        db.commit()
        db.refresh(db_job_app)

        return {
            "success": True,
            "message": "Job application updated successfully",
            "data": {
                "id": db_job_app.id,
                "job_title": db_job_app.job_title
            }
        }
    except Exception as error:
        logger.error(error)
        raise Exception("Error updating job application")


def delete_job_application(job_id: str, user: User, db: Session):
    try:
        db_job_app = db.query(JobApplication).filter(JobApplication.id == job_id,
                                                     JobApplication.user_id == user.id,
                                                     JobApplication.is_archived == False).first()
        if db_job_app is None:
            raise Exception("Job application not found")
        db_job_app.is_archived = True
        db.commit()
        db.refresh(db_job_app)
        return {
            "success": True,
            "message": "Job application deleted successfully"
        }
    except Exception:
        raise Exception("Error deleting job application")


def transition_job_application_status(db: Session, job_id: str, data: JobApplicationStatusTransition):
    try:
        db_job_app = db.query(JobApplication).filter(JobApplication.id == job_id).first()
        if db_job_app is None:
            raise Exception("Job application not found")
        db.close()
        result = job_application_state_machine.transition_state(db_job_app, data.to_status, JobApplicationStatusTransitionType.MANUAL, metadata={"reason": data.reason})
        return ApiResponse(success=True, payload=result)
    except Exception as error:
        logger.error(error)
        raise Exception(str(error))
