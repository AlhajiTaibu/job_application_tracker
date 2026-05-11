from app.core.celery import celery_app
from app.core.logging_config import logger
from app.core.util import resolve_bucket_name
from app.database import SessionLocal
from app.models.documents import Documents
from app.services.document_service import DocumentService


@celery_app.task(bind=True,  max_retries=3)
def upload_document_task(self, data: dict, file_content: str):
    try:
        bucket_name = resolve_bucket_name(data["purpose"])
        document_service = DocumentService(bucket_name)
        response = document_service.upload_file(data=data, file_content=file_content)
        logger.info(f"response: {response}")
        update_document(data['doc_id'], status="completed", file_key=response['file_key'])
        return response
    except Exception as error:
        if self.request.retries >= self.max_retries:
            update_document(data['doc_id'], status="failed", error=str(error))
        raise self.retry(exc=error, countdown=2 ** self.request.retries)


@celery_app.task()
def upload_image_task(data: dict, file_content: str):
    try:
        document_service = DocumentService("images")
        response = document_service.upload_image(data=data, file_content=file_content)
        logger.info(f"response: {response}")
        return response
    except Exception as error:
        logger.error(error)
        raise Exception(str(error))


@celery_app.task()
def delete_image_task(file_key: str):
    try:
        document_service = DocumentService("images")
        response = document_service.delete_image(file_key=file_key)
        logger.info(f"response: {response}")
        return response
    except Exception as error:
        logger.error(error)
        raise Exception(str(error))


def update_document(document_id, status=None, error=None, file_key=None):
    db = SessionLocal()
    try:
        if error is not None:
            db.query(Documents).filter(Documents.id == document_id).update({
                "status": status,
                "file_key": file_key
            })
            db.commit()
        else:
            db.query(Documents).filter(Documents.id == document_id).update({
                "status": status,
                "file_key": file_key,
                "error": error
            })
            db.commit()
    finally:
        db.close()