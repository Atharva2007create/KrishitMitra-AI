from pathlib import PurePath
from typing import Annotated, Any
from uuid import UUID, uuid4

import boto3  # type: ignore[import-untyped]
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import get_settings
from app.db.connection import get_db
from app.models.entities import ChatSession, MessageAttachment
from app.models.enums import AttachmentStatus, AttachmentType
from app.schemas.assistance import (
    AttachmentResponse,
    AttachmentUploadRequest,
    AttachmentUploadResponse,
)
from app.security.dependencies import FarmerUser

router = APIRouter(prefix="/attachments", tags=["attachment foundation"])
Session = Annotated[AsyncSession, Depends(get_db)]
ALLOWED_MIME_TYPES = {
    AttachmentType.IMAGE: {"image/jpeg", "image/png", "image/webp"},
    AttachmentType.DOCUMENT: {"application/pdf"},
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
    key = f"attachments/{current_user.id}/{attachment_id}/{payload.file_name}"
    client: Any = boto3.client("s3", region_name=settings.aws_region)
    presigned = client.generate_presigned_post(
        Bucket=bucket,
        Key=key,
        Fields={"Content-Type": payload.mime_type, "x-amz-server-side-encryption": "AES256"},
        Conditions=[
            {"Content-Type": payload.mime_type},
            {"x-amz-server-side-encryption": "AES256"},
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
        status=AttachmentStatus.PENDING_UPLOAD,
    )
    session.add(attachment)
    await session.commit()
    return AttachmentUploadResponse(
        attachment_id=attachment.id,
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
    if attachment.status != AttachmentStatus.PENDING_UPLOAD:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Invalid attachment state")
    attachment.status = AttachmentStatus.PENDING_ANALYSIS
    await session.commit()
    await session.refresh(attachment)
    return attachment


@router.get("/{attachment_id}", response_model=AttachmentResponse)
async def get_attachment(
    attachment_id: UUID, current_user: FarmerUser, session: Session
) -> MessageAttachment:
    return await _owned_attachment(session, current_user.id, attachment_id)
