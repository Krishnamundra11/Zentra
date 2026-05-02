"""S3 image upload helper. Fallback to local storage if AWS creds not provided."""
import os
import aioboto3
from app.config import settings


async def upload_image(image_bytes: bytes, task_id: str, content_type: str) -> str:
    """Upload image bytes to S3 or local disk and return the object key."""
    ext = content_type.split("/")[-1]
    key = f"uploads/{task_id}.{ext}"

    if not settings.aws_access_key_id or not settings.aws_secret_access_key:
        # Fallback to local storage
        os.makedirs("uploads", exist_ok=True)
        with open(key, "wb") as f:
            f.write(image_bytes)
        return key

    session = aioboto3.Session(
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        region_name=settings.aws_region,
    )
    async with session.client("s3") as s3:
        await s3.put_object(
            Bucket=settings.s3_bucket,
            Key=key,
            Body=image_bytes,
            ContentType=content_type,
        )
    return key
