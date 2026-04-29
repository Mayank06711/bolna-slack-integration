from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from app.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class Base(DeclarativeBase):
    pass


class DatabaseManager:

    def __init__(self, database_url: str):
        self._engine = create_async_engine(
            database_url,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            echo=False,
        )
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        logger.info(
            "Database engine created",
            extra={"extra_data": {"pool_size": 5, "max_overflow": 10}},
        )

    @property
    def engine(self):
        return self._engine

    async def get_session(self) -> AsyncSession:
        return self._session_factory()

    async def check_connection(self) -> bool:
        try:
            async with self._engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception as exc:
            logger.error(
                "Database connection check failed",
                extra={"extra_data": {"error": str(exc)}},
            )
            return False

    async def close(self) -> None:
        await self._engine.dispose()
        logger.info("Database engine disposed")


_db_manager: DatabaseManager | None = None


def get_db_manager() -> DatabaseManager:
    global _db_manager
    if _db_manager is None:
        settings = get_settings()
        _db_manager = DatabaseManager(settings.database_url)
    return _db_manager
