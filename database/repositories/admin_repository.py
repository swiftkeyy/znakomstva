"""Admin repository — roles, reports, verification queue."""
from typing import List, Optional

import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.admin import AdminRole, Report, VerificationQueue

logger = structlog.get_logger(__name__)


class AdminRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ── Roles ──────────────────────────────────────────────────────────────────

    async def get_role(self, telegram_id: int) -> Optional[str]:
        result = await self.session.execute(
            select(AdminRole.role).where(AdminRole.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def set_role(self, telegram_id: int, role: str, granted_by: int) -> None:
        existing = await self.session.execute(
            select(AdminRole).where(AdminRole.telegram_id == telegram_id)
        )
        obj = existing.scalar_one_or_none()
        if obj:
            obj.role = role
        else:
            self.session.add(AdminRole(telegram_id=telegram_id, role=role, granted_by=granted_by))
        await self.session.flush()

    async def remove_role(self, telegram_id: int) -> None:
        result = await self.session.execute(
            select(AdminRole).where(AdminRole.telegram_id == telegram_id)
        )
        obj = result.scalar_one_or_none()
        if obj:
            await self.session.delete(obj)
            await self.session.flush()

    async def list_admins(self) -> List[AdminRole]:
        result = await self.session.execute(select(AdminRole))
        return list(result.scalars().all())

    # ── Reports ────────────────────────────────────────────────────────────────

    async def create_report(self, reporter_id: int, reported_id: int, reason: str, comment: Optional[str] = None) -> Report:
        report = Report(reporter_id=reporter_id, reported_id=reported_id, reason=reason, comment=comment)
        self.session.add(report)
        await self.session.flush()
        await self.session.refresh(report)
        return report

    async def get_pending_reports(self, limit: int = 20) -> List[Report]:
        result = await self.session.execute(
            select(Report).where(Report.status == "pending").order_by(Report.created_at).limit(limit)
        )
        return list(result.scalars().all())

    async def resolve_report(self, report_id: int, resolved_by: int, status: str) -> None:
        await self.session.execute(
            update(Report).where(Report.id == report_id).values(status=status, resolved_by=resolved_by)
        )
        await self.session.flush()

    async def count_pending_reports(self) -> int:
        from sqlalchemy import func, select
        result = await self.session.execute(
            select(func.count()).where(Report.status == "pending")
        )
        return result.scalar() or 0

    # ── Verification Queue ─────────────────────────────────────────────────────

    async def add_to_queue(self, user_id: int, level: int, file_id: str, media_type: str = "photo") -> VerificationQueue:
        # Remove existing pending for same user+level
        existing = await self.session.execute(
            select(VerificationQueue).where(
                VerificationQueue.user_id == user_id,
                VerificationQueue.level == level,
                VerificationQueue.status == "pending",
            )
        )
        for obj in existing.scalars().all():
            await self.session.delete(obj)

        item = VerificationQueue(user_id=user_id, level=level, file_id=file_id, media_type=media_type)
        self.session.add(item)
        await self.session.flush()
        await self.session.refresh(item)
        return item

    async def get_pending_verifications(self, limit: int = 10) -> List[VerificationQueue]:
        result = await self.session.execute(
            select(VerificationQueue).where(VerificationQueue.status == "pending").order_by(VerificationQueue.created_at).limit(limit)
        )
        return list(result.scalars().all())

    async def get_verification(self, item_id: int) -> Optional[VerificationQueue]:
        result = await self.session.execute(
            select(VerificationQueue).where(VerificationQueue.id == item_id)
        )
        return result.scalar_one_or_none()

    async def resolve_verification(self, item_id: int, reviewed_by: int, status: str, reject_reason: Optional[str] = None) -> None:
        await self.session.execute(
            update(VerificationQueue).where(VerificationQueue.id == item_id).values(
                status=status, reviewed_by=reviewed_by, reject_reason=reject_reason
            )
        )
        await self.session.flush()

    async def count_pending_verifications(self) -> int:
        from sqlalchemy import func
        result = await self.session.execute(
            select(func.count()).where(VerificationQueue.status == "pending")
        )
        return result.scalar() or 0
