from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.connection import get_db
from app.models.entities import ChatSession, FaqItem, Feedback, ImageAnalysis, Message
from app.schemas.domain import FeedbackCreate, FeedbackResponse
from app.security.dependencies import FarmerUser

router = APIRouter(prefix="/feedback", tags=["feedback"])
Session = Annotated[AsyncSession, Depends(get_db)]


@router.post("", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def create_feedback(
    payload: FeedbackCreate, current_user: FarmerUser, session: Session
) -> Feedback:
    if payload.message_id is not None:
        message = await session.scalar(
            select(Message)
            .join(ChatSession)
            .where(Message.id == payload.message_id, ChatSession.user_id == current_user.id)
        )
        if message is None:
            raise HTTPException(status_code=404, detail="Message not found")
    if payload.image_analysis_id is not None:
        analysis = await session.scalar(
            select(ImageAnalysis).where(
                ImageAnalysis.id == payload.image_analysis_id,
                ImageAnalysis.user_id == current_user.id,
            )
        )
        if analysis is None:
            raise HTTPException(status_code=404, detail="Image analysis not found")
    if payload.faq_id is not None:
        faq = await session.scalar(
            select(FaqItem).where(FaqItem.id == payload.faq_id, FaqItem.is_active.is_(True))
        )
        if faq is None:
            raise HTTPException(status_code=404, detail="FAQ not found")
    feedback = Feedback(user_id=current_user.id, **payload.model_dump())
    session.add(feedback)
    await session.commit()
    await session.refresh(feedback)
    return feedback
