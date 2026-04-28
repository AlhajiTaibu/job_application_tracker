import base64
from uuid import uuid4
import io
from PIL import Image, ImageOps
from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging_config import logger
from app.models.user import Profile, User
from app.schemas.job_application import ApiResponse
from app.schemas.profile import ProfileUpdate
from app.tasks.document_tasks import upload_image_task, delete_image_task

AVATAR_SIZE = (400, 400)


def update_profile(data: ProfileUpdate, user_id: str, db: Session):
    try:
        profile = db.query(Profile).filter(Profile.user_id == user_id).first()
        if not profile:
            raise Exception("Profile not found")
        profile.first_name = data.first_name if data.first_name else profile.first_name
        profile.last_name = data.last_name if data.last_name else profile.last_name
        profile.title = data.title if data.title else profile.title
        profile.notification_type = data.notification_type if data.notification_type else profile.notification_type
        db.close()
        profile.save_to_db()
        return {
            "success": True,
            "message": "Profile updated successfully",
            "data": {
                "id": profile.id,
                "notification_type": profile.notification_type
            }
        }
    except Exception as error:
        logger.error(error)
        raise Exception("Error updating profile")


def get_profile(user_id: str, db: Session):
    try:
        stmt = select(
            User.email,
            Profile.id,
            Profile.first_name,
            Profile.last_name,
            Profile.title,
            Profile.notification_type,
            Profile.avatar_url).join(Profile, User.id == Profile.user_id).where(User.id == user_id)
        result = db.execute(stmt).first()
        if not result:
            raise Exception("Not found")
        data = {
            "id": result.id,
            "email": result.email,
            "first_name": result.first_name,
            "last_name": result.last_name,
            "title": result.title,
            "notification_type": result.notification_type,
            "avatar_url": result.avatar_url
        }
        return ApiResponse(success=True, payload=data)
    except Exception as error:
        logger.error(error)
        raise Exception("Error retrieving profile")


async def upload_profile_avatar(user_id: str, db: Session, file: UploadFile):
    try:
        if file.content_type not in ["image/jpeg", "image/png"]:
            return Exception("Only JPEG and PNG allowed")

        max_file_size = settings.max_file_size
        if file.size > max_file_size:
            raise Exception("File too large")

        profile = db.query(Profile).filter(Profile.user_id == user_id).first()
        if not profile:
            raise Exception("Profile not found")

        content = await file.read()
        processed_content = process_avatar(content)
        if not processed_content:
            raise Exception("Error processing image")

        encoded_content = base64.b64encode(processed_content).decode("utf-8")
        filename, ext = file.filename.split(".") if file.filename else []
        file_key = f"{uuid4()}.{ext}"
        payload = {
            "file_size": file.size,
            "filename": file.filename,
            "file_key": file_key,
            "ext": ext
        }
        task = upload_image_task.delay(payload, encoded_content)
        logger.info(f"Task {task.id}, image upload sent")
        prev_avatar_url = profile.avatar_url
        avatar_url = f"https://{settings.file_storage_project_id}.supabase.co/storage/v1/object/public/images/{file_key}"
        profile.avatar_url = avatar_url
        db.close()
        profile.save_to_db()

        if prev_avatar_url:
            prev_file_key = prev_avatar_url.split("/")[-1]
            delete_image_task.delay(prev_file_key)
        return {
            "success": True,
            "message": "Image uploaded successfully",
            "avatar_url": profile.avatar_url
        }
    except Exception as error:
        logger.error(error)
        Exception(str(error))


def process_avatar(file_content):
    try:
        img = Image.open(io.BytesIO(file_content))
        img = ImageOps.exif_transpose(img)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        img.thumbnail(AVATAR_SIZE, Image.Resampling.LANCZOS)

        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=85, optimize=True)
        buffer.seek(0)
        return buffer.getvalue()
    except Exception as error:
        logger.error(error)
