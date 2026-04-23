import datetime

from fastapi import HTTPException
from sqlalchemy import select, or_, and_, desc, asc
from sqlalchemy.orm import Session

from app.core.logging_config import logger
from app.core.util import encode_cursor, decode_cursor, cast_to_column_type
from app.models.job_application import Interview, JobApplication
from app.schemas.interview import InterviewCreate, InterviewUpdate, InterviewFilterParams
from app.schemas.job_application import ApiResponse
from app.services.state_machine import job_application_state_machine, interview_state_machine


def create_interview(data: InterviewCreate, db: Session):
    try:
        job_application_instance = db.query(JobApplication).where(JobApplication.id == data.job_application_id).first()
        if not job_application_instance:
            raise HTTPException(status_code=400, detail="Error creating interview")
        interview_instance = Interview(
            job_application_id=data.job_application_id,
            format=data.format,
            round=data.round,
            interviewer_name=data.interviewer_name,
            notes=data.notes,
            timezone=data.timezone,
            estimated_duration=data.estimated_duration,
            actual_duration=data.actual_duration
        )
        if data.date:
            interview_instance.date = datetime.datetime.strptime(data.date, "%d/%m/%Y").date()
        if data.time:
            interview_instance.time = datetime.datetime.strptime(data.time, "%H:%M").time()
        interview_instance.save_to_db()
        db.close()
        if job_application_instance.status in ["saved", "applied"]:
            if job_application_instance.status == "saved":
                job_application_state_machine.transition_state(job_application_instance, "applied")
                job_application_state_machine.transition_state(job_application_instance, "screening")
            else:
                job_application_state_machine.transition_state(job_application_instance, "screening")
        return {
            "success": True,
            "message": "Interview created successfully",
            "data": {
                "id": interview_instance.id,
                "format": interview_instance.format
            }
        }
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=400, detail="Error creating interview")


def update_interview(data: InterviewUpdate, interview_id: str, db: Session):
    try:
        db_interview = db.query(Interview).where(Interview.id == interview_id).first()
        if not db_interview:
            raise HTTPException(status_code=400, detail="Error updating interview")
        db_interview.notes = data.notes if data.notes else db_interview.notes
        db_interview.format = data.format if data.format else db_interview.format
        db_interview.round = data.round if data.round else db_interview.round
        db_interview.outcome = data.outcome if data.outcome else db_interview.outcome
        db_interview.feedback = data.feedback if data.feedback else db_interview.feedback
        db_interview.interviewer_name = data.interviewer_name if data.interviewer_name else db_interview.interviewer_name
        db_interview.timezone = data.timezone if data.timezone else db_interview.timezone
        db_interview.date = datetime.datetime.strptime(data.date, "%d/%m/%Y").date() if data.date else db_interview.date
        db_interview.time = datetime.datetime.strptime(data.time, "%H:%M").time() if data.time else db_interview.time
        db.commit()
        db.refresh(db_interview)

        if data.outcome:
            interview_state_machine.transition_state(db_interview)

        return {
            "success": True,
            "message": "Interview updated successfully",
            "data": {
                "id": db_interview.id,
                "format": db_interview.format
            }
        }
    except Exception as error:
        logger.error(error)
        raise HTTPException(status_code=404, detail="Error updating interview")


def get_interview_by_id(interview_id: str, db: Session):
    try:
        db_interview = db.query(Interview).where(Interview.id == interview_id).first()
        if not db_interview:
            raise HTTPException(status_code=404, detail="Interview not found")
        return ApiResponse(success=True, payload=db_interview)
    except Exception as error:
        logger.error(error)
        raise HTTPException(status_code=404, detail="Error getting interview")


def get_interviews(job_application_id: str, db: Session, limit: int):
    try:
        db_interview = db.query(Interview).where(Interview.job_application_id == job_application_id).order_by(
            Interview.round).limit(limit).all()
        results = db_interview if db_interview else []
        return ApiResponse(success=True, payload={"data": results})
    except Exception as error:
        logger.error(error)
        raise HTTPException(status_code=404, detail="Error getting interview")


def delete_interview(interview_id: str, db: Session):
    try:
        db_interview = db.query(Interview).filter(Interview.id == interview_id).first()
        if db_interview is None:
            raise HTTPException(status_code=404, detail="Interview not found")
        db.delete(db_interview)
        db.commit()
        return {
            "success": True,
            "message": "Interview deleted successfully"
        }
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=404, detail="Error deleting interview")


def get_upcoming_interviews(user_id: str, db: Session, limit: int):
    try:
        period = datetime.date.today() + datetime.timedelta(days=14)
        now = datetime.date.today()
        stmt = (
            select(
                JobApplication.id,
                JobApplication.user_id,
                JobApplication.company_name,
                JobApplication.job_title,
                Interview.job_application_id,
                Interview.format,
                Interview.round,
                Interview.outcome,
                Interview.date,
                Interview.time
            )
            .join(Interview, JobApplication.id == Interview.job_application_id)
            .where(or_(Interview.outcome == "scheduled",Interview.outcome =="pending"))
            .where(JobApplication.user_id == user_id)
            .where(and_(Interview.date >= now, Interview.date <= period))
            .order_by(Interview.date)
            .limit(limit)
            .distinct()
        )
        results = db.execute(stmt).all()
        return ApiResponse(success=True, payload={"data": results})
    except Exception as error:
        logger.error(error)
        raise HTTPException(status_code=404, detail="Error getting interview")


def get_interviews_history(user_id: str, db: Session, filters: InterviewFilterParams, limit: int, cursor: str = None):
    try:
        stmt = (
            select(
                JobApplication.id,
                JobApplication.user_id,
                JobApplication.company_name,
                JobApplication.job_title,
                Interview.job_application_id,
                Interview.format,
                Interview.round,
                Interview.outcome,
                Interview.interviewer_name,
                Interview.date,
                Interview.time,
                Interview.created_at
            )
            .join(Interview, JobApplication.id == Interview.job_application_id)
            .where(JobApplication.user_id == user_id)
            .order_by(Interview.date)
            .limit(limit)
        )
        # Sorting
        sort_column = getattr(Interview, filters.sort_by)
        if filters.order == "desc":
            stmt = stmt.order_by(desc(sort_column), desc(Interview.id)).limit(limit + 1)
        else:
            stmt = stmt.order_by(asc(sort_column), asc(Interview.id)).limit(limit + 1)

        # Filtering
        if filters.outcome:
            stmt = stmt.where(Interview.outcome.ilike(f"%{filters.outcome}%"))
        if filters.format:
            stmt = stmt.where(Interview.format == filters.format)
        if filters.start_date:
            stmt = stmt.where(Interview.created_at >= filters.start_date)
        if filters.end_date:
            stmt = stmt.where(Interview.created_at <= filters.end_date)

        # Searching
        if filters.q:
            stmt = stmt.where(Interview.interviewer_name.ilike(f"%{filters.q}%"))

        if cursor:
            raw_val, last_id = decode_cursor(cursor)
            typed_val = cast_to_column_type(raw_val, sort_column)
            if filters.order == "desc":
                stmt = stmt.where(
                    or_(
                        sort_column < typed_val,
                        and_(sort_column == typed_val, Interview.id < last_id)
                    )
                )
            else:
                stmt = stmt.where(
                    or_(
                        sort_column > typed_val,
                        and_(sort_column == typed_val, Interview.id > last_id)
                    )
                )

        results = db.execute(stmt).all()
        next_cursor = None
        has_next_page = len(results) > limit
        db_interviews = results[:limit] if results else results

        if has_next_page and db_interviews:
            last_item = db_interviews[-1]
            try:
                last_item_key = retrieve_last_item_key(filters.sort_by, last_item)
                next_cursor = encode_cursor(last_item_key, last_item.id)
            except Exception as e:
                logger.error(e)
                next_cursor = None

        return ApiResponse(success=True, payload={"data": db_interviews, "next_cursor": next_cursor})
    except Exception as error:
        logger.error(error)
        raise HTTPException(status_code=404, detail="Error getting interview")

def retrieve_last_item_key(sort_val, last_item: Interview):
    if sort_val == "created_at":
        return last_item.created_at
    elif sort_val == "format":
        return last_item.format
    elif sort_val == "date":
        return last_item.date
    elif sort_val == "outcome":
        return last_item.outcome
    else:
        raise HTTPException(status_code=404, detail="Error retrieving last item key")