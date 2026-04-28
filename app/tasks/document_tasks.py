from app.core.celery import celery_app
from app.core.logging_config import logger
from app.services.document_service import DocumentService


@celery_app.task(name="upload_document")
def upload_document_task(data: dict, file_content: str):
    document_service = DocumentService("resumes")
    response = document_service.upload_file(data=data, file_content=file_content)
    logger.info(f"response: {response}")
    return response


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
