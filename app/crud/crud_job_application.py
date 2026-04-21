from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import desc, asc, or_, select, and_
from sqlalchemy.orm import Session

from app.core.logging_config import logger
from app.core.util import decode_cursor, encode_cursor, retrieve_last_item_key, cast_to_column_type
from app.models.job_application import JobApplication, JobApplicationStatusHistory, Interview
from app.models.user import User
from app.schemas import job_application
from app.schemas.job_application import ApiResponse, JobFilterParams

VALID_TRANSITIONS = {
    'saved': ["applied", "rejected", "withdrawn"],
    "applied": ["screening", "rejected", "withdrawn"],
    'screening': ['interviewing', 'rejected', 'withdrawn'],
    'interviewing': ['offer', 'rejected', 'withdrawn'],
    'offer': ['accepted', 'rejected', 'withdrawn'],
}


def validate_job_application_status_change(from_status, to_status: str):
    if to_status not in VALID_TRANSITIONS.get(from_status):
        return False
    return True


def create_job_application(data: job_application.JobApplicationCreate, user: User):
    try:
        job_application_instance = JobApplication(
            company_name=data.company_name,
            job_url=data.job_url,
            job_title=data.job_title,
            user_id=user.id,
            date_applied=datetime.now(),
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
        raise HTTPException(status_code=404, detail="Error creating job application")


def get_job_application_by_id(job_id: str, user: User, db: Session):
    try:
        db_job = db.query(JobApplication).filter(JobApplication.id == job_id,
                                                 JobApplication.user_id == user.id).first()
        if not db_job:
            raise HTTPException(status_code=404, detail="Job application not found")
        return ApiResponse(success=True, payload=db_job)
    except Exception as error:
        logger.error(error)
        raise HTTPException(status_code=404, detail="Error getting job application")


def get_job_applications(user: User, db: Session, filters: JobFilterParams, limit: int = 20, cursor: str = None):
    try:
        stmt = select(JobApplication).where(JobApplication.user_id == user.id, JobApplication.is_archived == False)

        # Sorting
        sort_column = getattr(JobApplication, filters.sort_by)
        if filters.order == "desc":
            stmt = stmt.order_by(desc(sort_column), desc(JobApplication.id)).limit(limit + 1)
        else:
            stmt = stmt.order_by(asc(sort_column), asc(JobApplication.id)).limit(limit + 1)

        # Filtering
        if filters.company_name:
            stmt = stmt.where(JobApplication.company.ilike(f"%{filters.company_name}%"))
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
        raise HTTPException(status_code=400, detail="Error getting job applications")


def update_job_application(
        data: job_application.JobApplicationUpdate,
        db: Session,
        job_id: str):
    try:
        db_job_app = db.query(JobApplication).filter(JobApplication.id == job_id).first()
        if db_job_app is None:
            raise HTTPException(status_code=404, detail="Job application not found")
        if data.status and not validate_job_application_status_change(db_job_app.status, data.status):
            raise HTTPException(status_code=400, detail="Invalid transition")

        from_status = db_job_app.status
        db_job_app.status = data.status if data.status else db_job_app.status
        db_job_app.notes = data.notes if data.notes else db_job_app.notes
        db_job_app.updated_at = datetime.now()
        db_job_app.company_name = data.company_name if data.company_name else db_job_app.company_name
        db_job_app.job_url = data.job_url if data.job_url else db_job_app.job_url
        db_job_app.job_title = data.job_title if data.job_title else db_job_app.job_title
        db_job_app.source = data.source if data.source else db_job_app.source
        db_job_app.contacts_id = data.contacts_id if data.contacts_id else db_job_app.contacts_id
        db.commit()
        db.refresh(db_job_app)

        if data.status and validate_job_application_status_change(from_status, data.status):
            job_status_history = JobApplicationStatusHistory(
                job_application_id=db_job_app.id,
                from_status=from_status,
                to_status=data.status,
                reason="Status changed"
            )
            job_status_history.save_to_db()

            if data.status == "interviewing":
                db_interview = db.query(Interview).filter(Interview.job_application_id == job_id).all()
                if not db_interview:
                    interview_instance = Interview(
                        job_application_id=db_job_app.id,
                        outcome="no decision yet"
                    )
                    interview_instance.save_to_db()

            if from_status == "interviewing" and data.status == "offer":
                db_interview = db.query(Interview).filter(Interview.job_application_id == job_id).order_by(
                    desc(Interview.created_at)).all()
                if not db_interview:
                    raise HTTPException(status_code=400, detail="Update Error")
                else:
                    db_interview = db_interview[-1]
                    db_interview.outcome = "passed"
                    db_interview.save_to_db()

            if from_status == "interviewing" and data.status in ['rejected', 'withdrawn']:
                db_interview = db.query(Interview).filter(Interview.job_application_id == job_id).order_by(
                    desc(Interview.created_at)).all()
                if not db_interview:
                    raise HTTPException(status_code=400, detail="Update Error")
                else:
                    db_interview = db_interview[-1]
                    db_interview.outcome = "failed"
                    db_interview.save_to_db()

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
        raise HTTPException(status_code=400, detail="Error updating job application")


def delete_job_application(job_id: str, user: User, db: Session):
    try:
        db_job_app = db.query(JobApplication).filter(JobApplication.id == job_id,
                                                     JobApplication.user_id == user.id,
                                                     JobApplication.is_archived == False).first()
        if db_job_app is None:
            raise HTTPException(status_code=404, detail="Job application not found")
        db_job_app.is_archived = True
        db.commit()
        db.refresh(db_job_app)
        return {
            "success": True,
            "message": "Job application deleted successfully"
        }
    except Exception:
        raise HTTPException(status_code=404, detail="Error deleting job application")
