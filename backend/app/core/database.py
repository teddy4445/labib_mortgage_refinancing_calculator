from collections.abc import AsyncIterator
import hashlib

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import select

from backend.app.core.config import get_settings


class Base(DeclarativeBase):
    pass


settings = get_settings()
connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
engine = create_async_engine(settings.database_url, echo=settings.debug, future=True, connect_args=connect_args)
SessionFactory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionFactory() as session:
        yield session


async def init_database() -> None:
    from backend.app import models  # noqa: F401

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    admin_email = "lazebnik.teddy@gmail.com"
    admin_username = "Admin"
    admin_first_name = "Teddy"
    admin_last_name = "Lazebnik"
    admin_password_hash = hashlib.sha256("LabibShami2026!".encode("utf-8")).hexdigest()

    async with SessionFactory() as session:
        result = await session.execute(select(models.User).where(models.User.email == admin_email))
        user = result.scalar_one_or_none()
        if user is None:
            result = await session.execute(select(models.User).where(models.User.username == admin_username))
            user = result.scalar_one_or_none()

        if user is None:
            user = models.User(
                username=admin_username,
                email=admin_email,
                password_hash=admin_password_hash,
                first_name=admin_first_name,
                last_name=admin_last_name,
                role=models.UserRole.ADMIN,
                status=models.UserStatus.ACTIVE,
                email_verified=True,
            )
            session.add(user)
        else:
            user.username = admin_username
            user.email = admin_email
            user.password_hash = admin_password_hash
            user.first_name = admin_first_name
            user.last_name = admin_last_name
            user.role = models.UserRole.ADMIN
            user.status = models.UserStatus.ACTIVE
            user.email_verified = True

        await session.commit()
