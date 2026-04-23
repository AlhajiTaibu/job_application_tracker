from typing import Annotated

from fastapi import HTTPException
from fastapi.params import Depends
from fastapi.routing import APIRouter
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.logging_config import logger
from app.crud import crud_contacts
from app.models.user import User
from app.schemas.contacts import ContactsCreate, ContactsUpdate, ContactsDetailResponse, \
    ContactsListResponse, ContactsLinkJobApplication
from app.schemas.job_application import ApiResponse

router = APIRouter()


@router.post("/create")
async def contacts(
        user: Annotated[User, Depends(get_current_user)],
        request_data: ContactsCreate
):
    try:
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Forbidden")
        return crud_contacts.create_contacts(data=request_data, user_id=user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/update/{contact_id}")
async def contacts(
        user: Annotated[User, Depends(get_current_user)],
        db: Annotated[Session,Depends(get_db)],
        request_data: ContactsUpdate,
        contact_id: str
):
    try:
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Forbidden")
        return crud_contacts.update_contacts(data=request_data, db=db, contact_id=contact_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/get/{contact_id}", response_model=ApiResponse[ContactsDetailResponse])
async def contacts(
        user: Annotated[User, Depends(get_current_user)],
        db: Annotated[Session,Depends(get_db)],
        contact_id: str
):
    try:
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Forbidden")
        return crud_contacts.get_contacts_by_id(contact_id=contact_id, user_id=user.id, db=db)
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.get("/list", response_model=ApiResponse[ContactsListResponse])
async def contacts(
        user: Annotated[User, Depends(get_current_user)],
        db: Annotated[Session, Depends(get_db)],
        limit: int = 20
):
    try:
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Forbidden")
        return crud_contacts.get_contacts(user_id=user.id, db=db, limit=limit)
    except Exception as error:
        logger.error(error)
        raise HTTPException(status_code=400, detail=str(error))


@router.delete("/delete/{contact_id}")
async def contacts(
        user: Annotated[User, Depends(get_current_user)],
        db: Annotated[Session, Depends(get_db)],
        contact_id: str
):
    try:
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Forbidden")
        return crud_contacts.delete_contacts(contact_id=contact_id, user_id=user.id, db=db)
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.post("/link-to-application/{contact_id}")
async def link_contact_to_job_application(
        user: Annotated[User, Depends(get_current_user)],
        db: Annotated[Session, Depends(get_db)],
        contact_id: str,
        request_data: ContactsLinkJobApplication

):
    try:
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Forbidden")
        return crud_contacts.link_contact_to_job_application(data=request_data, db=db, contact_id=contact_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))