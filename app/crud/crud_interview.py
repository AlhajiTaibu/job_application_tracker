from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.logging_config import logger
from app.models.job_application import Interview, JobApplication
from app.schemas.job_application import InterviewCreate, InterviewUpdate, ApiResponse
import datetime


def create_interview(data: InterviewCreate, db: Session):
    try:
        job_application_instance = db.query(JobApplication).where(JobApplication.id == data.job_application_id).first()
        if not job_application_instance:
            raise HTTPException(status_code=400, detail="Error creating interview")
        interview_instance = Interview(
            job_application_id=data.job_application_id,
            format=data.format,
            round=data.round,
            date=datetime.date.fromisoformat(data.date),
            time=datetime.time.fromisoformat(data.time)
        )
        interview_instance.save_to_db()
        return {
            "success": True,
            "message": "Interview created successfully",
            "data": {
                "id" : interview_instance.id,
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
        db_interview.notes = f"What went well:\n{data.what_went_well} \nWhat was discussed:\n{data.what_was_discussed}" \
            if data.what_went_well or data.what_was_discussed else db_interview.notes
        db_interview.format = data.format if data.format else db_interview.format
        db_interview.round = data.round if data.round else db_interview.round
        db_interview.date = datetime.datetime.strptime(data.date,"%d/%m/%Y").date() if data.date else db_interview.date
        db_interview.time = datetime.datetime.strptime(data.time, "%H:%M").time() if data.time else db_interview.time
        db.commit()
        db.refresh(db_interview)
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
        db_interview = db.query(Interview).where(Interview.job_application_id == job_application_id).limit(limit).all()
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

