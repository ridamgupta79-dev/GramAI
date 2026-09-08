"""Database layer — PostgreSQL (Neon/Supabase) with SQLite fallback.

Set DATABASE_URL in backend/.env to use Postgres; otherwise a local SQLite
file is used so development never blocks.
"""
from __future__ import annotations

import os
from datetime import datetime

from dotenv import load_dotenv
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

DATABASE_URL = os.getenv("DATABASE_URL", "")

if DATABASE_URL:
    # Neon/Supabase use postgres:// — SQLAlchemy needs postgresql://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    DB_KIND = "postgresql"
else:
    _sqlite_path = os.path.join(os.path.dirname(__file__), "..", "..", "gramai.db")
    engine = create_engine(f"sqlite:///{os.path.abspath(_sqlite_path)}", connect_args={"check_same_thread": False})
    DB_KIND = "sqlite"

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mobile: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120), default="")
    role: Mapped[str] = mapped_column(String(20), default="user")  # 'user' | 'admin'
    preferred_lang: Mapped[str] = mapped_column(String(8), default="en")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    analyses: Mapped[list["Analysis"]] = relationship(back_populates="user")


class Analysis(Base):
    __tablename__ = "analyses"
    id: Mapped[str] = mapped_column(String(16), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    village: Mapped[str] = mapped_column(String(120), default="")
    block: Mapped[str] = mapped_column(String(120))
    district: Mapped[str] = mapped_column(String(120))
    state: Mapped[str] = mapped_column(String(120))
    sector: Mapped[str] = mapped_column(String(60))
    margin_capital: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(20), default="completed")
    viability_score: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped[User] = relationship(back_populates="analyses")
    report: Mapped["Report | None"] = relationship(back_populates="analysis", uselist=False)


class Report(Base):
    __tablename__ = "reports"
    id: Mapped[str] = mapped_column(String(16), primary_key=True)
    analysis_id: Mapped[str] = mapped_column(ForeignKey("analyses.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(200), default="")
    content_json: Mapped[str] = mapped_column(Text)  # full dashboard payload
    share_url: Mapped[str | None] = mapped_column(String(300), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    analysis: Mapped[Analysis] = relationship(back_populates="report")


class Conversation(Base):
    __tablename__ = "conversations"
    id: Mapped[str] = mapped_column(String(24), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(200), default="New conversation")
    messages_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Application(Base):
    __tablename__ = "applications"
    id: Mapped[str] = mapped_column(String(16), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    report_id: Mapped[str] = mapped_column(String(16), index=True)
    scheme: Mapped[str] = mapped_column(String(120))
    applicant_name: Mapped[str] = mapped_column(String(120))
    phone: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), default="submitted")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


def init_db() -> None:
    Base.metadata.create_all(engine)
    _migrate()
    # Seed the admin account (idempotent)
    admin_mobile = os.getenv("ADMIN_MOBILE", "9999999999")
    with SessionLocal() as db:
        if not db.query(User).filter(User.mobile == admin_mobile).first():
            db.add(User(mobile=admin_mobile, full_name="GramAI Admin", role="admin"))
            db.commit()


def _migrate() -> None:
    """Lightweight column migrations for existing SQLite/Postgres tables."""
    import sqlite3
    if engine.url.get_backend_name() != "sqlite":
        return  # Postgres: run Alembic migrations in production
    with engine.connect() as conn:
        cols = [r[1] for r in conn.exec_driver_sql("PRAGMA table_info(users)")]
        if "role" not in cols:
            conn.exec_driver_sql("ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user'")
            conn.exec_driver_sql("UPDATE users SET role='user' WHERE role IS NULL")
            conn.commit()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
