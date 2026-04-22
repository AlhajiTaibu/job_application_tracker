import json
from typing import Annotated

from fastapi import UploadFile, File, HTTPException, Form
from fastapi.params import Depends
from fastapi.routing import APIRouter
from sqlalchemy.orm import Session


from app.api.deps import get_current_user, get_db
from app.crud import crud_documents
from app.models.user import User
from app.schemas.documents import DocumentsUpload

router = APIRouter()


@router.post("/upload")
async def upload_document(
        user: Annotated[User, Depends(get_current_user)],
        request_data: Annotated[DocumentsUpload, Depends(DocumentsUpload.as_form)],
        file: UploadFile = File(...)
):
    try:
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Forbidden")
        return await crud_documents.upload_document(file=file, data=request_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/view/{doc_id}")
async def view_document(
        user: Annotated[User, Depends(get_current_user)],
        db: Annotated[Session, Depends(get_db)],
        doc_id: str
):
    try:
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Forbidden")
        return crud_documents.view_document(db=db, doc_id=doc_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))