from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import AuditLog


def record_audit(
    session: AsyncSession,
    *,
    actor_user_id: UUID | None,
    action: str,
    entity_type: str,
    entity_id: UUID | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    session.add(
        AuditLog(
            actor_user_id=actor_user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            metadata_json=metadata,
        )
    )
