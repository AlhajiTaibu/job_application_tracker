import base64

from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session

from app.core.logging_config import logger
from app.core.util import resolve_bucket_name
from app.models.documents import Documents
from app.models.job_application import JobApplication
from app.schemas.documents import DocumentsUpload, DocumentsLinkJobApplication
from app.services.storage_service import storage_service
from app.tasks.document_tasks import upload_document_task


async def upload_document(file: UploadFile, data: DocumentsUpload, user_id: str):
    try:
        content = await file.read()
        encoded_content = base64.b64encode(content).decode("utf-8")
        payload = {
            "purpose": data.purpose,
            "file_size": file.size,
            "filename": file.filename,
            "user_id": user_id
        }
        if data.is_base:
            payload["is_base"] = data.is_base
        if data.name:
            payload["name"] = data.name
        if data.is_draft:
            payload["is_draft"] = data.is_draft
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
        bucket_name = resolve_bucket_name(db_doc.purpose)
        url = storage_service.get_signed_url(bucket_name, f"{db_doc.file_key}.{db_doc.file_type}")
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


def link_document_to_job_application(data: DocumentsLinkJobApplication, db: Session, doc_id: str):
    try:
        job = db.query(JobApplication).filter(JobApplication.id == data.job_application_id).first()
        if not job:
            raise Exception("Job Application not found")
        db_doc = db.query(Documents).filter(Documents.id == doc_id).first()
        if not db_doc:
            raise Exception("Document not found")
        db_doc.job_applications.append(job)
        db.commit()
        db.refresh(db_doc)
        return {
            "success": True,
            "message": "Document linked to job application successfully"
        }
    except Exception as error:
        logger.error(error)
        raise Exception("Error linking document to job application")


def unlink_document_to_job_application(db: Session, doc_id: str):
    try:
        db_doc = db.query(Documents).filter(Documents.id == doc_id).first()
        if not db_doc:
            raise Exception("Document not found")
        db_doc.job_applications.clear()
        db.commit()
        db.refresh(db_doc)
        return {
            "success": True,
            "message": "Document unlinked from job application successfully"
        }
    except Exception as error:
        logger.error(error)
        raise Exception("Error unlinking document from job application")


def get_all_documents(db: Session):
    try:
        pass
    except Exception as error:
        logger.error(error)
        raise Exception("Error retrieving documents")