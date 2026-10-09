import json
from datetime import UTC, datetime
from pathlib import PurePath
from typing import Annotated, Any
from uuid import UUID, uuid4

import boto3  # type: ignore[import-untyped]
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import get_settings
from app.db.connection import get_db
from app.models.entities import ChatSession, ImageAnalysis, MessageAttachment
from app.models.enums import AttachmentStatus, AttachmentType, RecordStatus
from app.schemas.assistance import (
    AttachmentResponse,
    AttachmentUploadRequest,
    AttachmentUploadResponse,
    ImageAnalysisResponse,
)
from app.security.dependencies import FarmerUser

router = APIRouter(prefix="/attachments", tags=["attachment foundation"])
Session = Annotated[AsyncSession, Depends(get_db)]
ALLOWED_MIME_TYPES = {
    AttachmentType.IMAGE: {"image/jpeg", "image/png", "image/webp"},
    AttachmentType.DOCUMENT: {"application/pdf"},
}
IMAGE_EXTENSIONS = {
    "image/jpeg": {".jpg", ".jpeg"},
    "image/png": {".png"},
    "image/webp": {".webp"},
}


async def _owned_attachment(
    session: AsyncSession, user_id: UUID, attachment_id: UUID
) -> MessageAttachment:
    value = await session.scalar(
        select(MessageAttachment).where(
            MessageAttachment.id == attachment_id, MessageAttachment.user_id == user_id
        )
    )
    if value is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found")
    return value


@router.post(
    "/upload", response_model=AttachmentUploadResponse, status_code=status.HTTP_201_CREATED
)
async def initiate_attachment_upload(
    payload: AttachmentUploadRequest,
    current_user: FarmerUser,
    session: Session,
) -> AttachmentUploadResponse:
    chat = await session.scalar(
        select(ChatSession).where(
            ChatSession.id == payload.chat_session_id, ChatSession.user_id == current_user.id
        )
    )
    if chat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")
    if PurePath(payload.file_name).name != payload.file_name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid file name"
        )
    if payload.mime_type not in ALLOWED_MIME_TYPES[payload.attachment_type]:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported attachment MIME type",
        )
    if payload.attachment_type == AttachmentType.IMAGE:
        extension = PurePath(payload.file_name).suffix.lower()
        if extension not in IMAGE_EXTENSIONS[payload.mime_type]:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Image file extension does not match its MIME type",
            )
    settings = get_settings()
    max_bytes = settings.attachment_max_size_mb * 1024 * 1024
    if payload.file_size > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE, detail="Attachment is too large"
        )
    bucket = (
        settings.aws_s3_bucket_images
        if payload.attachment_type == AttachmentType.IMAGE
        else settings.aws_s3_bucket_documents
    )
    if not bucket:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Attachment storage is not configured",
        )
    attachment_id = uuid4()
    key = f"farmer-uploads/{current_user.id}/{chat.id}/{attachment_id}/{payload.file_name}"
    metadata = {
        "attachment-id": str(attachment_id),
        "user-id": str(current_user.id),
        "session-id": str(chat.id),
        "source-type": payload.source_type.value,
    }
    client: Any = boto3.client("s3", region_name=settings.aws_region)
    presigned = client.generate_presigned_post(
        Bucket=bucket,
        Key=key,
        Fields={
            "Content-Type": payload.mime_type,
            "x-amz-server-side-encryption": "AES256",
            **{f"x-amz-meta-{name}": value for name, value in metadata.items()},
        },
        Conditions=[
            {"Content-Type": payload.mime_type},
            {"x-amz-server-side-encryption": "AES256"},
            *[{f"x-amz-meta-{name}": value} for name, value in metadata.items()],
            ["content-length-range", 1, max_bytes],
        ],
        ExpiresIn=settings.presigned_upload_ttl_seconds,
    )
    attachment = MessageAttachment(
        id=attachment_id,
        user_id=current_user.id,
        chat_session_id=chat.id,
        attachment_type=payload.attachment_type,
        source_type=payload.source_type,
        file_name=payload.file_name,
        mime_type=payload.mime_type,
        file_size=payload.file_size,
        s3_key=key,
        bucket_name=bucket,
        status=AttachmentStatus.PENDING_UPLOAD,
    )
    session.add(attachment)
    await session.flush()
    analysis: ImageAnalysis | None = None
    if payload.attachment_type == AttachmentType.IMAGE:
        analysis = ImageAnalysis(
            user_id=current_user.id,
            crop_cycle_id=chat.crop_cycle_id,
            attachment_id=attachment_id,
            s3_key=key,
            model_name=settings.image_analysis_model,
            status=RecordStatus.PENDING,
        )
        session.add(analysis)
    await session.commit()
    return AttachmentUploadResponse(
        attachment_id=attachment.id,
        analysis_id=analysis.id if analysis else None,
        upload_url=str(presigned["url"]),
        form_fields={str(key): str(value) for key, value in presigned["fields"].items()},
        mime_type=payload.mime_type,
        max_size_bytes=max_bytes,
        expires_in_seconds=settings.presigned_upload_ttl_seconds,
    )


@router.post("/{attachment_id}/complete", response_model=AttachmentResponse)
async def complete_attachment_upload(
    attachment_id: UUID, current_user: FarmerUser, session: Session
) -> MessageAttachment:
    attachment = await _owned_attachment(session, current_user.id, attachment_id)
    if attachment.status not in (
        AttachmentStatus.PENDING_UPLOAD,
        AttachmentStatus.PROCESSING,
        AttachmentStatus.COMPLETED,
    ):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Invalid attachment state")
    settings = get_settings()
    if not attachment.bucket_name or not attachment.s3_key:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Attachment storage metadata is missing"
        )
    client: Any = boto3.client("s3", region_name=settings.aws_region)
    try:
        uploaded = client.head_object(Bucket=attachment.bucket_name, Key=attachment.s3_key)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Uploaded object could not be verified",
        ) from exc
    actual_size = int(uploaded.get("ContentLength", 0))
    actual_type = str(uploaded.get("ContentType", "")).lower()
    max_bytes = settings.attachment_max_size_mb * 1024 * 1024
    if actual_size < 1 or actual_size > max_bytes or actual_size != attachment.file_size:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Uploaded object size does not match the upload request",
        )
    if actual_type != attachment.mime_type.lower():
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Uploaded object content type does not match the upload request",
        )
    metadata = {str(key).lower(): str(value) for key, value in uploaded.get("Metadata", {}).items()}
    expected_metadata = {
        "attachment-id": str(attachment.id),
        "user-id": str(attachment.user_id),
        "session-id": str(attachment.chat_session_id),
        "source-type": attachment.source_type.value,
    }
    if any(metadata.get(name) != value for name, value in expected_metadata.items()):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Uploaded object metadata is invalid",
        )
    attachment.s3_etag = str(uploaded.get("ETag", "")).strip('"') or None
    attachment.content_sha256 = uploaded.get("ChecksumSHA256")
    attachment.upload_confirmed_at = datetime.now(UTC)
    if attachment.status == AttachmentStatus.PENDING_UPLOAD:
        attachment.status = (
            AttachmentStatus.PENDING_ANALYSIS
            if attachment.attachment_type == AttachmentType.IMAGE
            else AttachmentStatus.UPLOADED
        )
    await session.commit()
    await session.refresh(attachment)
    return attachment


@router.post("/{attachment_id}/analyze", response_model=ImageAnalysisResponse)
async def request_image_analysis(
    attachment_id: UUID, current_user: FarmerUser, session: Session
) -> ImageAnalysis:
    attachment = await _owned_attachment(session, current_user.id, attachment_id)
    if attachment.attachment_type != AttachmentType.IMAGE:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only image attachments can be analyzed",
        )
    if attachment.status not in (
        AttachmentStatus.PENDING_ANALYSIS,
        AttachmentStatus.PROCESSING,
        AttachmentStatus.COMPLETED,
    ):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Image is not ready")
    analysis = await session.scalar(
        select(ImageAnalysis).where(
            ImageAnalysis.attachment_id == attachment.id,
            ImageAnalysis.user_id == current_user.id,
        )
    )
    if analysis is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")
    if attachment.status == AttachmentStatus.PENDING_ANALYSIS:
        settings = get_settings()
        client: Any = boto3.client("lambda", region_name=settings.aws_region)
        client.invoke(
            FunctionName=settings.image_analysis_lambda_name,
            InvocationType="Event",
            Payload=json.dumps(
                {
                    "Records": [
                        {
                            "eventSource": "krishimitra.api",
                            "s3": {
                                "bucket": {"name": attachment.bucket_name},
                                "object": {"key": attachment.s3_key},
                            },
                        }
                    ]
                }
            ).encode(),
        )
    return analysis


@router.get("/{attachment_id}", response_model=AttachmentResponse)
async def get_attachment(
    attachment_id: UUID, current_user: FarmerUser, session: Session
) -> MessageAttachment:
    return await _owned_attachment(session, current_user.id, attachment_id)
