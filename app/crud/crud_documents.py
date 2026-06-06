import base64
from datetime import datetime

from fastapi import UploadFile
from sqlalchemy import select, desc, asc
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging_config import logger
from app.core.util import resolve_bucket_name
from app.models.association import documents_association_table
from app.models.documents import Documents
from app.models.job_application import JobApplication
from app.schemas.documents import DocumentsUpload, DocumentsLinkJobApplication, DocumentFilterParams, DocumentUpdate
from app.schemas.job_application import ApiResponse
from app.services.storage_service import storage_service
from app.tasks.document_tasks import upload_document_task


def check_document_extension_vs_purpose(ext: str, purpose: str):
    if purpose == "cv" and ext == "pdf":
        return True
    if purpose == "cover letter" and ext in ["pdf", "doc", "txt", "docx"]:
        return True
    if purpose == "portfolio" and ext in ["jpeg", "jpg", "png", "pdf", "doc", "txt", "docx"]:
        return True
    return False


async def upload_document(file: UploadFile, data: DocumentsUpload, user_id: str):
    try:
        file_size = file.size if file.size else 4 * settings.max_file_size
        if data.purpose in ["cv", "cover letter", "portfolio"] and file.size and file.size > settings.max_file_size:
            raise Exception("File too large")
        if data.purpose == "other" and file.size and file.size > 2 * settings.max_file_size:
            raise Exception("File too large")
        if not file.filename:
            raise Exception("No file provided")

        filename, ext = file.filename.split(".") if file.filename else []
        if not check_document_extension_vs_purpose(ext, data.purpose):
            raise Exception("Invalid file format")

        content = await file.read()
        encoded_content = base64.b64encode(content).decode("utf-8")
        doc_instance = Documents(
            size=file_size,
            file_type=ext,
            filename=filename,
            purpose=data.purpose,
            user_id=user_id,
            upload_date=datetime.now()
        )

        if data.is_base:
            doc_instance.is_base = data.is_base
        if data.is_draft:
            doc_instance.is_draft = data.is_draft
        if data.name:
            doc_instance.name = data.name
        doc_instance.save_to_db()
        payload = {
            "ext": ext,
            "doc_id": str(doc_instance.id),
            "purpose": doc_instance.purpose
        }
        task = upload_document_task.delay(payload, encoded_content)
        logger.info(f"Task {task.id}, document upload sent")
        return {
            "success": True,
            "message": "Document uploaded successfully",
            "task_id": task.id,
            "doc_id": doc_instance.id
        }
    except Exception as error:
        logger.error(error)
        raise Exception("Error uploading document")


def view_document(db: Session, doc_id: str):
    try:
        db_doc = db.query(Documents).filter(Documents.id == doc_id, Documents.is_archived == False).first()
        if not db_doc:
            raise Exception("Document not found")
        bucket_name = resolve_bucket_name(str(db_doc.purpose))
        url = storage_service.get_signed_url(bucket_name, f"{db_doc.file_key}.{db_doc.file_type}")
        return {"url": url}
    except Exception as error:
        logger.error(error)
        raise Exception("Error retrieving document")


def delete_document(db: Session, doc_id: str):
    try:
        db_doc = db.query(Documents).filter(Documents.id == doc_id).first()
        if not db_doc:
            raise Exception("Document not found")
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
        raise Exception("Error deleting document")


def link_document_to_job_application(data: DocumentsLinkJobApplication, db: Session, doc_id: str):
    try:
        job = db.query(JobApplication).filter(JobApplication.id == data.job_application_id).first()
        if not job:
            raise Exception("Job Application not found")
        db_doc = db.query(Documents).filter(Documents.id == doc_id).first()
        if not db_doc:
            raise Exception("Document not found")
        if job not in db_doc.job_applications:
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


def unlink_document_to_job_application(data: DocumentsLinkJobApplication, db: Session, doc_id: str):
    try:
        db_doc = db.query(Documents).filter(Documents.id == doc_id).first()
        if not db_doc:
            raise Exception("Document not found")
        job = db.query(JobApplication).filter(JobApplication.id == data.job_application_id).first()
        if not job:
            raise Exception("Job Application not found")
        db_doc.job_applications.remove(job)
        db.commit()
        db.refresh(db_doc)
        return {
            "success": True,
            "message": "Document unlinked from job application successfully"
        }
    except Exception as error:
        logger.error(error)
        raise Exception("Error unlinking document from job application")


def get_all_documents(db: Session, filters: DocumentFilterParams, limit: int, user_id: str):
    try:
        stmt = (select(Documents)
                .outerjoin(documents_association_table, documents_association_table.c.documents_id == Documents.id)
                .where(Documents.user_id == user_id)
                .where(Documents.is_archived == False).distinct())

        sort_column = getattr(Documents, filters.sort_by)

        if filters.company_name:
            stmt = (stmt.join(JobApplication, JobApplication.id == documents_association_table.c.job_application_id)
                    .where(JobApplication.company_name.ilike(f"%{filters.company_name}%")))
        if filters.purpose:
            stmt = stmt.where(Documents.purpose == filters.purpose)

        if filters.q:
            stmt = (stmt.join(JobApplication, JobApplication.id == documents_association_table.c.job_application_id)
                    .where(JobApplication.company_name.ilike(f"%{filters.q}%")))

        if filters.order == "desc":
            stmt = stmt.order_by(desc(sort_column))
        else:
            stmt = stmt.order_by(asc(sort_column))

        stmt = stmt.limit(limit + 1)
        results = db.execute(stmt).unique().scalars().all()
        return ApiResponse(success=True, payload={"data": results})
    except Exception as error:
        logger.error(error)
        raise Exception("Error retrieving documents")


def get_document_status(db: Session, doc_id: str):
    try:
        db_doc = db.query(Documents).filter(Documents.id == doc_id).first()
        if not db_doc:
            raise Exception("Document not found")
        return {
        "status": db_doc.status,
        "error": db_doc.error
    }
    except Exception as error:
        logger.error(error)
        raise Exception("Error retrieving document status")


def update_document(db: Session, doc_id: str, data: DocumentUpdate):
    try:
        db_doc = db.query(Documents).filter(Documents.id == doc_id).first()
        if not db_doc:
            raise Exception("Document not found")
        if data.is_submitted is not None:
            db_doc.is_submitted = data.is_submitted
        if data.name:
            db_doc.name = data.name
        if data.is_draft is not None:
            db_doc.is_draft = data.is_draft
        if data.is_base is not None:
            db_doc.is_base = data.is_base
        db.commit()
        db.refresh(db_doc)
        return {
            "success": True,
            "message": "Document updated successfully"
        }
    except Exception as error:
        logger.error(error)
        raise Exception("Error updating document")