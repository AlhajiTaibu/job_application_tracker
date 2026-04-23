import base64

from app.core.celery import celery_app
from app.core.logging_config import logger
from app.services.document_service import DocumentService


@celery_app.task(name="upload_document")
def upload_document_task(data: dict, file_content: str):
        document_service = DocumentService()
        response = document_service.upload_file(data=data, file_content=file_content)
        logger.info(f"response: {response}")
        return response