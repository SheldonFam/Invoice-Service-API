import ssl
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


def _prepare_database_url(url: str) -> tuple[str, dict]:
    """Strip asyncpg-incompatible query params and build connect_args."""
    connect_args: dict = {}
    parsed = urlparse(url)

    is_remote = "localhost" not in (parsed.hostname or "") and "127.0.0.1" not in (
        parsed.hostname or ""
    )

    if is_remote:
        ssl_context = ssl.create_default_context()
        connect_args["ssl"] = ssl_context
        # Disable prepared statement caching for Neon's connection pooler
        connect_args["statement_cache_size"] = 0
        connect_args["prepared_statement_cache_size"] = 0

    # Remove params that asyncpg doesn't understand
    if parsed.query:
        params = parse_qs(parsed.query)
        params.pop("sslmode", None)
        params.pop("channel_binding", None)
        clean_query = urlencode(params, doseq=True)
        parsed = parsed._replace(query=clean_query)

    return urlunparse(parsed), connect_args


clean_url, connect_args = _prepare_database_url(settings.DATABASE_URL)

engine = create_async_engine(
    clean_url,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    connect_args=connect_args,
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass
