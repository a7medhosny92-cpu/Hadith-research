"""SQLAlchemy engine/session for the production PostgreSQL store.

The dev path (FTS over JSONL) needs none of this. On the production install
(psycopg + pgvector) this backs persistent storage and the hybrid lexical+semantic
search. Engine creation is lazy, so importing the app never opens a connection.
"""

from __future__ import annotations

from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    return create_engine(get_settings().database_url, pool_pre_ping=True, future=True)


@lru_cache(maxsize=1)
def _maker() -> sessionmaker:
    return sessionmaker(bind=get_engine(), expire_on_commit=False, future=True)


def new_session() -> Session:
    return _maker()()
