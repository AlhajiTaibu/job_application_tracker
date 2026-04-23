import base64

from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session

from app.core.logging_config import logger
from app.models.documents import Documents
from app.schemas.documents import DocumentsUpload
from app.services.storage_service import storage_service
from app.tasks.document_tasks import upload_document_task


async def upload_document(file: UploadFile, data: DocumentsUpload):
    try:
        content = await file.read()
        encoded_content = base64.b64encode(content).decode("utf-8")
        payload = {
            "job_application_id": data.job_application_id,
            "purpose": data.purpose,
            "file_size": file.size,
            "filename": file.filename
        }
        task = upload_document_task.delay(payload, encoded_content)
        logger.info(f"Task {task.id}, document upload sent")
        return {
            "success": True,
            "message": "Document uploaded successfully"
        }
    except Exception as error:
        logger.error(error)
        raise HTTPException(status_code=400, detail="Error uploading document")


def view_document(db: Session, doc_id: str):
    try:
        db_doc = db.query(Documents).filter(Documents.id == doc_id, Documents.is_archived == False).first()
        if not db_doc:
            raise HTTPException(status_code=404, detail="Document not found")
        url = storage_service.get_signed_url("resumes", f"{db_doc.file_key}.{db_doc.file_type}")
        return {"url": url}
    except Exception as error:
        logger.error(error)
        raise HTTPException(status_code=400, detail="Error retrieving document")


def delete_document(db: Session, doc_id: str):
    try:
        db_doc = db.query(Documents).filter(Documents.id == doc_id).first()
        if not db_doc:
            raise HTTPException(status_code=404, detail="Document not found")
        db_doc.is_archived = True
        db_doc.is_latest = False
        db.commit()
        db.refresh(db_doc)
        return {
            "success": True,
            "message": "Document deleted successfully"
        }
    except Exception as error:
        logger.error(error)
        raise HTTPException(status_code=400, detail="Error deleting document")
