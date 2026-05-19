import base64
from uuid import uuid4

from app.core.config import settings
from app.core.logging_config import logger
from app.database import SessionLocal
from app.services.storage_service import storage_service


class DocumentService:
    def __init__(self, bucket):
        self.db = SessionLocal()
        self.bucket = bucket
        self.resume_max_file_size = settings.max_file_size

    def upload_file(self, data, file_content):
        try:
            file_key = f"{uuid4()}.{data['ext']}"
            content = base64.b64decode(file_content)
            extension = self.resolve_ext(data['ext'])
            storage_service.upload_file(content, self.bucket, extension, file_key)
            final_file_key = file_key.split('.')[0]
            return {
                "success": True,
                "message": "Document uploaded successfully",
                "file_key": final_file_key
            }
        except Exception as error:
            logger.error(error)
            raise Exception(str(error))

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
