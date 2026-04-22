import boto3
from botocore.config import Config
from app.core.config import settings

class DocumentStorage:
    def __init__(self):
        self.project_id = settings.file_storage_project_id
        self.access_key_id = settings.file_storage_access_key_id
        self.secret_access_key = settings.file_storage_secret_access_key
        self.region_name = settings.file_storage_region_name
        config = Config(
            signature_version="s3v4",
            s3={
                'addressing_style': 'path',
            }
        )
        self.s3 = boto3.client(
            "s3",
            endpoint_url=f"https://{self.project_id}.supabase.co/storage/v1/s3",
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
            region_name=self.region_name,
            config=config
        )

    def upload_file(self, file_content, bucket: str, extension: str, file_key: str):
        self.s3.put_object(
            Bucket=bucket,
            Key=file_key,
            Body=file_content,
            ContentType="application/pdf" if extension == "pdf" else "image/jpeg"
        )
        return file_key

    def get_signed_url(self, bucket: str, file_key: str, expires_in: int = 3600):
        return self.s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket, 'Key': file_key},
            ExpiresIn=expires_in
        )

storage_service = DocumentStorage()