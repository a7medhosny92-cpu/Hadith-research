"""ORM tables for the production store (PostgreSQL + pgvector).

Mirrors the parsed JSONL — one row per hadith, one per sharh chunk — each with an
``embedding`` column for vector similarity. Created and populated by
``scripts.load_db`` (runs on the production install; needs psycopg + pgvector).

The same fields the dev FTS index serves are stored here, so the API's search
interface can be re-pointed from sqlite to a hybrid SQL backend without touching
callers.
"""

from __future__ import annotations

from pgvector.sqlalchemy import Vector
from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.config import get_settings

_DIM = get_settings().embedding_dim


class Base(DeclarativeBase):
    pass


class Hadith(Base):
    __tablename__ = "hadith"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    book_id: Mapped[int] = mapped_column(Integer, index=True)
    collection: Mapped[str | None] = mapped_column(String(128))
    number: Mapped[int | None] = mapped_column(Integer, index=True)
    matn: Mapped[str] = mapped_column(Text)
    matn_norm: Mapped[str] = mapped_column(Text)  # folded, for lexical/trgm search
    isnad: Mapped[str | None] = mapped_column(Text)
    grade: Mapped[str | None] = mapped_column(String(64), index=True)
    chapter: Mapped[str | None] = mapped_column(Text)
    page: Mapped[int | None] = mapped_column(Integer)
    volume: Mapped[str | None] = mapped_column(String(32))
    embedding: Mapped[list[float] | None] = mapped_column(Vector(_DIM), nullable=True)


class SharhPassage(Base):
    __tablename__ = "sharh_passage"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    book_id: Mapped[int] = mapped_column(Integer, index=True)
    sharh_name: Mapped[str | None] = mapped_column(String(256))
    base_id: Mapped[int | None] = mapped_column(Integer, index=True)
    base_name: Mapped[str | None] = mapped_column(String(128))
    hadith_number: Mapped[int | None] = mapped_column(Integer, index=True)
    chapter: Mapped[str | None] = mapped_column(Text)
    page: Mapped[int | None] = mapped_column(Integer)
    page_id: Mapped[int | None] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    text_norm: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(_DIM), nullable=True)


# After load, create ANN + trigram indexes for hybrid search, e.g.:
#   CREATE INDEX ON hadith USING hnsw (embedding vector_cosine_ops);
#   CREATE INDEX ON hadith USING gin (matn_norm gin_trgm_ops);
