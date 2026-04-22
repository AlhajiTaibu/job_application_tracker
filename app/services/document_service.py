import base64
from datetime import datetime
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging_config import logger
from app.database import SessionLocal
from app.models.documents import Documents
from app.models.job_application import JobApplication
from app.services.storage_service import storage_service


class DocumentService:
    def __init__(self):
        self.db = SessionLocal()
        self.bucket = "resumes"

    def upload_file(self, data, file_content):
        try:
            max_file_size = settings.max_file_size
            if data['file_size'] > max_file_size:
                raise HTTPException(status_code=413, detail="File too large")

            db_job = self.db.query(JobApplication).filter(JobApplication.id == data['job_application_id']).first()
            if not db_job:
                raise HTTPException(status_code=404, detail="Job application not found")

            doc = self.db.query(Documents).filter(Documents.job_application_id == data['job_application_id'],
                                             Documents.is_latest == True, Documents.purpose == data['purpose']).order_by(
                desc(Documents.created_at)).first()
            if doc:
                doc.is_latest = False
                self.db.commit()

            filename, ext = data['filename'].split(".") if data['filename'] else []
            if not self.check_document_extension_vs_purpose(ext, data['purpose']):
                raise HTTPException(status_code=400, detail="Invalid file format")
            file_key = f"{uuid4()}.{ext}"
            content = base64.b64decode(file_content)
            storage_service.upload_file(content, self.bucket, ext, file_key)
            final_file_key = file_key.split('.')[0]

            doc_instance = Documents(
                job_application_id=data['job_application_id'],
                size=data['file_size'],
                file_type=ext,
                filename=filename,
                file_key=final_file_key,
                purpose=data['purpose'],
                upload_date=datetime.now(),
                version_name=db_job.job_title,
                is_latest=True
            )
            doc_instance.save_to_db()
            return {
                "success": True,
                "message": "Document uploaded successfully",
                "id": doc_instance.id
            }
        except Exception as error:
            logger.error(error)
            raise HTTPException(status_code=400, detail="Error uploading document")

    def check_document_extension_vs_purpose(self, ext: str, purpose: str):
        if purpose == "cv" and ext == "pdf":
            return True
        if purpose == "cover letter" and ext in ["pdf", "doc", "txt", "docx"]:
            return True
        if purpose == "portfolio" and ext in ["jpeg", "jpg", "png"]:
            return True
        return False