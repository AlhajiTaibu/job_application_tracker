from typing import Annotated

from fastapi import HTTPException
from fastapi.params import Depends
from fastapi.routing import APIRouter
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.crud import crud_interview
from app.models.user import User
from app.schemas.job_application import InterviewCreate, InterviewUpdate, ApiResponse, InterviewDetail, InterviewList

router = APIRouter()


@router.post("/create")
async def interview(
        user: Annotated[User, Depends(get_current_user)],
        db: Annotated[Session, Depends(get_db)],
        request_data: InterviewCreate
):
    try:
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Forbidden")
        return crud_interview.create_interview(data=request_data, db=db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/update/{interview_id}")
async def interview(
        user: Annotated[User, Depends(get_current_user)],
        db: Annotated[Session, Depends(get_db)],
        request_data: InterviewUpdate,
        interview_id: str
):
    try:
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Forbidden")
        return crud_interview.update_interview(data=request_data, interview_id=interview_id, db=db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/get/{interview_id}", response_model=ApiResponse[InterviewDetail])
async def interview(
        user: Annotated[User, Depends(get_current_user)],
        db: Annotated[Session, Depends(get_db)],
        interview_id: str
):
    try:
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Forbidden")
        return crud_interview.get_interview_by_id(interview_id=interview_id, db=db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/list/{job_id}", response_model=ApiResponse[InterviewList] )
async def interviews(
        user: Annotated[User, Depends(get_current_user)],
        db: Annotated[Session, Depends(get_db)],
        job_id: str,
        limit: int = 20
):
    try:
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Forbidden")
        return crud_interview.get_interviews(job_application_id=job_id, db=db, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/delete/{interview_id}")
async def interview(
        user: Annotated[User, Depends(get_current_user)],
        db: Annotated[Session, Depends(get_db)],
        interview_id: str
):
    try:
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Forbidden")
        return crud_interview.delete_interview(interview_id=interview_id, db=db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
