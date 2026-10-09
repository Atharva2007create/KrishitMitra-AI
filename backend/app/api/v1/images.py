import json
from contextlib import suppress
from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

import boto3  # type: ignore[import-untyped]
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import get_settings
from app.db.connection import get_db
from app.models.entities import ImageAnalysis, MessageAttachment
from app.models.enums import AttachmentStatus, RecordStatus
from app.schemas.assistance import ImageAnalysisResponse
from app.security.dependencies import FarmerUser

router = APIRouter(prefix="/image-analyses", tags=["crop image analysis"])
Session = Annotated[AsyncSession, Depends(get_db)]


async def _sync_result(analysis: ImageAnalysis, session: AsyncSession) -> ImageAnalysis:
    if analysis.status in (
        RecordStatus.COMPLETED,
        RecordStatus.FAILED,
        RecordStatus.IMAGE_INSUFFICIENT,
    ):
        return analysis
    if analysis.attachment_id is None:
        return analysis
    attachment = await session.get(MessageAttachment, analysis.attachment_id)
    if attachment is None or not attachment.bucket_name:
        return analysis
    client: Any = boto3.client("s3", region_name=get_settings().aws_region)
    try:
        response = client.get_object(
            Bucket=attachment.bucket_name,
            Key=f"analysis-results/{attachment.id}.json",
        )
        raw = response["Body"].read(1_000_001)
        if len(raw) > 1_000_000:
            return analysis
        value = json.loads(raw)
    except Exception:
        return analysis
    if not isinstance(value, dict) or value.get("attachment_id", str(attachment.id)) != str(
        attachment.id
    ):
        return analysis
    raw_status = str(value.get("status", ""))
    if raw_status not in {item.value for item in RecordStatus}:
        return analysis
    analysis.status = RecordStatus(raw_status)
    analysis.content_hash = value.get("content_hash")
    reported_model = value.get("model")
    if isinstance(reported_model, str) and reported_model.strip():
        analysis.model_name = reported_model.strip()
    analysis.quality_assessment = value.get("quality_assessment")
    analysis.observed_symptoms = value.get("observed_symptoms")
    analysis.candidate_issues = value.get("candidate_issues")
    analysis.evidence_json = value.get("evidence")
    analysis.error_code = value.get("error_code")
    processed_at = value.get("processed_at")
    if isinstance(processed_at, str):
        with suppress(ValueError):
            analysis.processed_at = datetime.fromisoformat(processed_at)
    if analysis.status == RecordStatus.PROCESSING:
        attachment.status = AttachmentStatus.PROCESSING
    elif analysis.status == RecordStatus.FAILED:
        attachment.status = AttachmentStatus.FAILED
    elif analysis.status in (RecordStatus.COMPLETED, RecordStatus.IMAGE_INSUFFICIENT):
        attachment.status = AttachmentStatus.COMPLETED
    await session.commit()
    await session.refresh(analysis)
    return analysis


@router.get("/{analysis_id}", response_model=ImageAnalysisResponse)
async def get_image_analysis(
    analysis_id: UUID, current_user: FarmerUser, session: Session
) -> ImageAnalysis:
    value = await session.scalar(
        select(ImageAnalysis).where(
            ImageAnalysis.id == analysis_id, ImageAnalysis.user_id == current_user.id
        )
    )
    if value is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")
    return await _sync_result(value, session)
