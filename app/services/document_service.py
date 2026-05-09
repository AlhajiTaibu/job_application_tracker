import base64
from datetime import datetime
from uuid import uuid4

from app.core.config import settings
from app.core.logging_config import logger
from app.database import SessionLocal
from app.models.documents import Documents
from app.services.storage_service import storage_service


class DocumentService:
    def __init__(self, bucket):
        self.db = SessionLocal()
        self.bucket = bucket
        self.resume_max_file_size = settings.max_file_size

    def upload_file(self, data, file_content):
        try:
            if data['purpose'] in ["cv", "cover letter", "portfolio"] and data['file_size'] > self.resume_max_file_size:
                raise Exception("File too large")
            if data['purpose'] == "other" and data['file_size'] > 2 * self.resume_max_file_size:
                raise Exception("File too large")
            filename, ext = data['filename'].split(".") if data['filename'] else []
            if not self.check_document_extension_vs_purpose(ext, data['purpose']):
                raise Exception("Invalid file format")
            file_key = f"{uuid4()}.{ext}"
            content = base64.b64decode(file_content)
            extension = self.resolve_ext(ext)
            storage_service.upload_file(content, self.bucket, extension, file_key)
            final_file_key = file_key.split('.')[0]

            doc_instance = Documents(
                size=data['file_size'],
                file_type=ext,
                filename=filename,
                file_key=final_file_key,
                purpose=data['purpose'],
                user_id=data['user_id'],
                upload_date=datetime.now()
            )
            if "is_base" in data:
                doc_instance.is_base = data['is_base']
            if "name" in data:
                doc_instance.name = data['name']
            if "is_draft" in data:
                doc_instance.is_draft = data['is_draft']
            doc_instance.save_to_db()
            return {
                "success": True,
                "message": "Document uploaded successfully",
                "id": doc_instance.id
            }
        except Exception as error:
            logger.error(error)
            raise Exception(str(error))

    def check_document_extension_vs_purpose(self, ext: str, purpose: str):
        if purpose == "cv" and ext == "pdf":
            return True
        if purpose == "cover letter" and ext in ["pdf", "doc", "txt", "docx"]:
            return True
        if purpose == "portfolio" and ext in ["jpeg", "jpg", "png"]:
            return True
        return False

    def upload_image(self, data, file_content):
        try:
            file_key = data['file_key']
            ext = self.resolve_ext(data['ext'])
            content = base64.b64decode(file_content)
            return storage_service.upload_file(content, self.bucket, ext, file_key)
        except Exception as error:
            raise Exception(str(error))

    def delete_image(self, file_key):
        try:
            storage_service.delete_file(self.bucket, file_key)
        except Exception as error:
            logger.error(error)
            raise Exception(str(error))

    def resolve_ext(self, ext: str):
        if ext == "pdf":
            return "application/pdf"
        elif ext == "jpeg":
            return "image/jpeg"
        elif ext == "jpg":
            return "image/jpg"
        elif ext == "png":
            return "image/png"
        else:
            return "application/octet-stream"
