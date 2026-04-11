from __future__ import annotations

from collections.abc import Sequence
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import Select, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from backend.app import models
from backend.app.schemas import AnalyticsEventIn, CustomerRequestIn, MortgageInput, RecommendationResult, UserCreate


class DataBaseManager:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    @asynccontextmanager
    async def session_scope(self) -> AsyncSession:
        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def add(self, instance: models.Base) -> models.Base:
        async with self.session_scope() as session:
            session.add(instance)
            await session.flush()
            await session.refresh(instance)
            return instance

    async def save(self, instance: models.Base) -> models.Base:
        async with self.session_scope() as session:
            merged = await session.merge(instance)
            await session.flush()
            await session.refresh(merged)
            return merged

    async def delete(self, model: type[models.Base], object_id: int) -> bool:
        async with self.session_scope() as session:
            result = await session.execute(delete(model).where(model.id == object_id))  # type: ignore[attr-defined]
            return bool(result.rowcount)

    async def get_by_id(self, model: type[models.Base], object_id: int) -> models.Base | None:
        async with self.session_scope() as session:
            return await session.get(model, object_id)

    async def search(
        self,
        query: Select[Any],
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[Any]:
        async with self.session_scope() as session:
            result = await session.execute(query.limit(limit).offset(offset))
            return result.scalars().all()

    async def filter(
        self,
        model: type[models.Base],
        **filters: Any,
    ) -> Sequence[models.Base]:
        query = select(model)
        for field_name, value in filters.items():
            if value is None:
                continue
            query = query.where(getattr(model, field_name) == value)
        return await self.search(query)

    async def create_user(self, payload: UserCreate, password_hash: str) -> models.User:
        user = models.User(
            username=payload.username,
            email=str(payload.email),
            password_hash=password_hash,
            phone_number=payload.phone_number,
            first_name=payload.first_name,
            last_name=payload.last_name,
            age=payload.age,
            gender=payload.gender,
            marital_status=payload.marital_status,
            occupation=payload.occupation,
            holding_period_years=payload.holding_period_years,
            risk_tolerance=payload.risk_tolerance,
            payment_sensitivity=payload.payment_sensitivity,
            preference_goal=payload.preference_goal,
            inflation_aversion=payload.inflation_aversion,
            reset_risk_aversion=payload.reset_risk_aversion,
        )
        return await self.add(user)

    async def find_user_by_email(self, email: str) -> models.User | None:
        async with self.session_scope() as session:
            result = await session.execute(select(models.User).where(models.User.email == email))
            return result.scalar_one_or_none()

    async def find_user_by_username(self, username: str) -> models.User | None:
        async with self.session_scope() as session:
            result = await session.execute(select(models.User).where(models.User.username == username))
            return result.scalar_one_or_none()

    async def update_user_password(self, user_id: int, password_hash: str) -> models.User | None:
        async with self.session_scope() as session:
            user = await session.get(models.User, user_id)
            if user is None:
                return None
            user.password_hash = password_hash
            await session.flush()
            await session.refresh(user)
            return user

    async def find_password_reset_token(self, token: str) -> models.PasswordResetToken | None:
        async with self.session_scope() as session:
            result = await session.execute(
                select(models.PasswordResetToken).where(models.PasswordResetToken.token == token)
            )
            return result.scalar_one_or_none()

    async def consume_password_reset_token(self, token: models.PasswordResetToken) -> models.PasswordResetToken:
        token.consumed_at = datetime.utcnow()
        return await self.save(token)

    async def update_user_status(self, user_id: int, status: models.UserStatus) -> models.User | None:
        async with self.session_scope() as session:
            user = await session.get(models.User, user_id)
            if user is None:
                return None
            user.status = status
            await session.flush()
            await session.refresh(user)
            return user

    async def list_users(self, *, status: str | None = None, search_term: str | None = None) -> list[models.User]:
        query = select(models.User).order_by(models.User.created_at.desc())
        if status:
            query = query.where(models.User.status == status)
        if search_term:
            token = f"%{search_term.lower()}%"
            query = query.where(
                func.lower(models.User.username).like(token) | func.lower(models.User.email).like(token)
            )

        async with self.session_scope() as session:
            result = await session.execute(query)
            return list(result.scalars().all())

    async def get_latest_mortgage(self, user_id: int) -> models.Mortgage | None:
        async with self.session_scope() as session:
            result = await session.execute(
                select(models.Mortgage)
                .where(models.Mortgage.user_id == user_id)
                .order_by(models.Mortgage.created_at.desc())
                .options(selectinload(models.Mortgage.tracks))
            )
            return result.scalars().first()

    async def create_mortgage(
        self,
        user_id: int,
        payload: MortgageInput,
        *,
        raw_payload: dict[str, Any] | None = None,
    ) -> models.Mortgage:
        mortgage = models.Mortgage(
            user_id=user_id,
            lender_name=payload.lender_name,
            property_city=payload.property_city,
            property_value=payload.property_value,
            current_monthly_payment=payload.current_monthly_payment,
            loan_purpose=payload.loan_purpose,
            occupancy_status=payload.occupancy_status,
            outstanding_balance_total=sum(track.outstanding_balance for track in payload.tracks),
            estimated_refinance_cost=payload.prepayment_fee + payload.advisor_cost + payload.bank_cost + payload.appraisal_cost,
            raw_payload=raw_payload or payload.model_dump(mode="json"),
        )

        for track in payload.tracks:
            mortgage.tracks.append(
                models.MortgageTrack(
                    label=track.label,
                    track_type=track.track_type,
                    outstanding_balance=track.outstanding_balance,
                    current_rate=track.current_rate,
                    remaining_term_months=track.remaining_term_months,
                    linkage_type=track.linkage_type,
                    rate_type=track.rate_type,
                    reset_interval=track.reset_interval,
                    next_reset_date=track.next_reset_date,
                    amortization_method=track.amortization_method,
                    prepayment_penalty_rule=track.prepayment_penalty_rule,
                )
            )

        return await self.add(mortgage)

    async def create_analysis_run(self, *, mortgage_id: int, result: RecommendationResult) -> models.AnalysisRun:
        raw_output = result.model_dump(mode="json")
        recommendation_code = (
            result.recommendation_summary.recommendation_code
            if result.recommendation_summary is not None
            else result.explanation
        )
        selected_total_cost = Decimal(str(result.assumptions.get("selected_total_refinance_cost", "0")))
        analysis_run = models.AnalysisRun(
            mortgage_id=mortgage_id,
            recommendation_type=recommendation_code,
            should_act_now=result.should_act_now,
            current_payment=result.current_monthly_payment,
            proposed_payment=result.projected_monthly_payment,
            projected_net_savings=result.projected_net_savings,
            upfront_costs=selected_total_cost,
            break_even_month=result.break_even_month,
            npv=result.npv,
            risk_reduction_summary=", ".join(result.explanation_tokens) if result.explanation_tokens else None,
            explanation=result.explanation,
            assumptions=result.assumptions,
            raw_output=raw_output,
        )
        return await self.add(analysis_run)

    async def get_latest_analysis_run(self, mortgage_id: int) -> models.AnalysisRun | None:
        async with self.session_scope() as session:
            result = await session.execute(
                select(models.AnalysisRun)
                .where(models.AnalysisRun.mortgage_id == mortgage_id)
                .order_by(models.AnalysisRun.created_at.desc())
            )
            return result.scalars().first()

    async def create_alert(
        self,
        *,
        user_id: int,
        title: str,
        message: str,
        severity: str,
        source: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> models.Alert:
        alert = models.Alert(
            user_id=user_id,
            title=title,
            message=message,
            severity=severity,
            source=source,
            payload=payload or {},
        )
        return await self.add(alert)

    async def list_alerts(self, *, user_id: int) -> list[models.Alert]:
        async with self.session_scope() as session:
            result = await session.execute(
                select(models.Alert).where(models.Alert.user_id == user_id).order_by(models.Alert.created_at.desc())
            )
            return list(result.scalars().all())

    async def update_alert_status(self, alert_id: int, status: models.AlertStatus) -> models.Alert | None:
        async with self.session_scope() as session:
            alert = await session.get(models.Alert, alert_id)
            if alert is None:
                return None
            alert.status = status
            await session.flush()
            await session.refresh(alert)
            return alert

    async def create_request(
        self,
        payload: CustomerRequestIn,
        *,
        status: models.RequestStatus | None = None,
    ) -> models.CustomerRequest:
        request = models.CustomerRequest(
            user_id=payload.user_id,
            request_type=payload.request_type,
            status=status or models.RequestStatus.OPEN,
            source_page=payload.source_page,
            notes=payload.notes,
            details=payload.details,
        )
        return await self.add(request)

    async def get_latest_request(
        self,
        *,
        user_id: int | None = None,
        request_type: str | None = None,
        status: models.RequestStatus | None = None,
    ) -> models.CustomerRequest | None:
        query = select(models.CustomerRequest).order_by(models.CustomerRequest.created_at.desc())
        if user_id is not None:
            query = query.where(models.CustomerRequest.user_id == user_id)
        if request_type is not None:
            query = query.where(models.CustomerRequest.request_type == request_type)
        if status is not None:
            query = query.where(models.CustomerRequest.status == status)

        async with self.session_scope() as session:
            result = await session.execute(query)
            return result.scalars().first()

    async def log_analytics_event(self, payload: AnalyticsEventIn) -> models.AnalyticsEvent:
        event = models.AnalyticsEvent(
            user_id=payload.user_id,
            session_id=payload.session_id,
            event_type=payload.event_type,
            page=payload.page,
            traffic_source=payload.traffic_source,
            event_metadata=payload.metadata,
        )
        return await self.add(event)

    async def log_error(
        self,
        *,
        service: str,
        category: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> models.ErrorEvent:
        return await self.add(
            models.ErrorEvent(service=service, category=category, message=message, details=details or {})
        )

    async def upsert_market_source(
        self,
        *,
        source_key: str,
        display_name: str,
        status: models.DataSourceStatus,
        last_success_at: datetime | None = None,
        last_error: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> models.MarketDataSource:
        async with self.session_scope() as session:
            existing = await session.scalar(
                select(models.MarketDataSource).where(models.MarketDataSource.source_key == source_key)
            )
            if existing is None:
                existing = models.MarketDataSource(source_key=source_key, display_name=display_name)
                session.add(existing)

            existing.display_name = display_name
            existing.status = status
            existing.last_attempt_at = datetime.utcnow()
            if last_success_at is not None or existing.last_success_at is None:
                existing.last_success_at = last_success_at
            if last_error is not None or status != models.DataSourceStatus.FAILED:
                existing.last_error = last_error
            existing.source_metadata = metadata or {}
            await session.flush()
            await session.refresh(existing)
            return existing

    async def add_market_snapshot(
        self,
        *,
        source_id: int,
        payload: dict[str, Any],
        as_of: datetime | None = None,
    ) -> models.MarketDataSnapshot:
        snapshot = models.MarketDataSnapshot(source_id=source_id, payload=payload, as_of=as_of or datetime.utcnow())
        return await self.add(snapshot)

    async def admin_overview(self) -> dict[str, Any]:
        async with self.session_scope() as session:
            user_count = await session.scalar(select(func.count()).select_from(models.User)) or 0
            mortgage_count = await session.scalar(select(func.count()).select_from(models.Mortgage)) or 0
            open_request_count = await session.scalar(
                select(func.count()).select_from(models.CustomerRequest).where(
                    models.CustomerRequest.status == models.RequestStatus.OPEN
                )
            ) or 0
            active_alert_count = await session.scalar(
                select(func.count()).select_from(models.Alert).where(models.Alert.status == models.AlertStatus.ACTIVE)
            ) or 0
            users = (
                await session.execute(select(models.User).order_by(models.User.created_at.desc()).limit(25))
            ).scalars().all()
            data_sources = (
                await session.execute(
                    select(models.MarketDataSource).order_by(models.MarketDataSource.updated_at.desc())
                )
            ).scalars().all()

            since = datetime.utcnow() - timedelta(days=30)
            usage_rows = (
                await session.execute(
                    select(
                        func.date(models.AnalyticsEvent.created_at).label("day"),
                        func.count().label("total"),
                    )
                    .where(models.AnalyticsEvent.created_at >= since)
                    .where(models.AnalyticsEvent.event_type == "wizard_started")
                    .group_by("day")
                    .order_by("day")
                )
            ).all()
            help_rows = (
                await session.execute(
                    select(
                        func.date(models.CustomerRequest.created_at).label("day"),
                        func.count().label("total"),
                    )
                    .where(models.CustomerRequest.created_at >= since)
                    .group_by("day")
                    .order_by("day")
                )
            ).all()

        return {
            "metrics": {
                "users": user_count,
                "mortgages": mortgage_count,
                "open_requests": open_request_count,
                "active_alerts": active_alert_count,
            },
            "wizard_usage": usage_rows,
            "help_requests": help_rows,
            "users": list(users),
            "data_sources": list(data_sources),
        }
