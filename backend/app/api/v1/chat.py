from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.connection import get_db
from app.models.entities import ChatSession, CropCycle, Farm, FarmerProfile, Message
from app.models.enums import SenderType
from app.schemas.domain import (
    ChatSessionCreate,
    ChatSessionResponse,
    ChatSessionUpdate,
    MessageCreate,
    MessageResponse,
)
from app.security.dependencies import FarmerUser

router = APIRouter(prefix="/chat/sessions", tags=["chat foundation"])
Session = Annotated[AsyncSession, Depends(get_db)]


async def _owned_session(session: AsyncSession, user_id: UUID, session_id: UUID) -> ChatSession:
    chat = await session.scalar(
        select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == user_id)
    )
    if chat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")
    return chat


async def _assert_owned_cycle(session: AsyncSession, user_id: UUID, cycle_id: UUID) -> None:
    value = await session.scalar(
        select(CropCycle.id)
        .join(Farm)
        .join(FarmerProfile)
        .where(CropCycle.id == cycle_id, FarmerProfile.user_id == user_id)
    )
    if value is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Crop cycle not found")


@router.post("", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_chat_session(
    payload: ChatSessionCreate, current_user: FarmerUser, session: Session
) -> ChatSession:
    if payload.crop_cycle_id is not None:
        await _assert_owned_cycle(session, current_user.id, payload.crop_cycle_id)
    chat = ChatSession(user_id=current_user.id, **payload.model_dump())
    session.add(chat)
    await session.commit()
    await session.refresh(chat)
    return chat


@router.get("", response_model=list[ChatSessionResponse])
async def list_chat_sessions(current_user: FarmerUser, session: Session) -> list[ChatSession]:
    return list(
        await session.scalars(
            select(ChatSession)
            .where(ChatSession.user_id == current_user.id)
            .order_by(ChatSession.updated_at.desc())
        )
    )


@router.get("/{session_id}", response_model=ChatSessionResponse)
async def get_chat_session(
    session_id: UUID, current_user: FarmerUser, session: Session
) -> ChatSession:
    return await _owned_session(session, current_user.id, session_id)


@router.patch("/{session_id}", response_model=ChatSessionResponse)
async def update_chat_session(
    session_id: UUID,
    payload: ChatSessionUpdate,
    current_user: FarmerUser,
    session: Session,
) -> ChatSession:
    chat = await _owned_session(session, current_user.id, session_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(chat, field, value)
    await session.commit()
    await session.refresh(chat)
    return chat


@router.post(
    "/{session_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED
)
async def create_user_message(
    session_id: UUID,
    payload: MessageCreate,
    current_user: FarmerUser,
    session: Session,
) -> Message:
    chat = await _owned_session(session, current_user.id, session_id)
    message = Message(chat_session_id=chat.id, sender_type=SenderType.USER, content=payload.content)
    chat.last_message_at = datetime.now(UTC)
    session.add(message)
    await session.commit()
    await session.refresh(message)
    return message


@router.get("/{session_id}/messages", response_model=list[MessageResponse])
async def list_messages(
    session_id: UUID, current_user: FarmerUser, session: Session
) -> list[Message]:
    await _owned_session(session, current_user.id, session_id)
    return list(
        await session.scalars(
            select(Message)
            .where(Message.chat_session_id == session_id)
            .order_by(Message.created_at)
        )
    )
