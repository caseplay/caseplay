"""Persistent application models with compatible MySQL and local SQLite storage."""
import os
from datetime import datetime
from pathlib import Path
from sqlalchemy import create_engine, inspect, text, String, Text, Integer, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from sqlalchemy.engine import URL
from utils.db import config


def now():
    return datetime.utcnow()


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    display_name: Mapped[str] = mapped_column(String(80), default='学习者')
    remaining_plays: Mapped[int] = mapped_column(Integer, default=100)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    last_login: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class LoginToken(Base):
    __tablename__ = 'login_tokens'
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)


class PlaySession(Base):
    __tablename__ = 'sessions'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    script_id: Mapped[str] = mapped_column(String(255))
    character_name: Mapped[str] = mapped_column(String(255))
    chat_history: Mapped[list] = mapped_column(JSON, default=list)
    script_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    current_scene: Mapped[str] = mapped_column(Text, default='')
    status: Mapped[str] = mapped_column(String(20), default='ongoing')
    end_report: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    evidence_used: Mapped[list] = mapped_column(JSON, default=list)
    events: Mapped[list] = mapped_column(JSON, default=list)
    reflection: Mapped[str] = mapped_column(Text, default='')
    report_data: Mapped[dict] = mapped_column(JSON, default=dict)
    is_busy: Mapped[bool] = mapped_column(Boolean, default=False)
    busy_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Favorite(Base):
    __tablename__ = 'favorites'
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), primary_key=True)
    script_id: Mapped[str] = mapped_column(String(255), primary_key=True)


class ScriptDraft(Base):
    __tablename__ = 'script_drafts'
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    payload: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(20), default='draft')
    created_by: Mapped[int] = mapped_column(ForeignKey('users.id'))
    reviewed_by: Mapped[int | None] = mapped_column(Integer, nullable=True)
    review_note: Mapped[str] = mapped_column(Text, default='')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


def make_storage():
    settings = config.get('mysql', {})
    url = os.getenv('DATABASE_URL') or URL.create('mysql+pymysql', username=settings.get('user'), password=settings.get('password'), host=settings.get('host'), port=int(settings.get('port', 3306)), database=settings.get('database', 'lmt'), query={'charset': 'utf8mb4'})
    sqlite = str(url).startswith('sqlite')
    engine = create_engine(url, pool_pre_ping=True, connect_args={'check_same_thread': False, 'timeout': 30} if sqlite else {})
    if sqlite:
        from sqlalchemy import event
        @event.listens_for(engine, 'connect')
        def sqlite_options(conn, _):
            conn.execute('PRAGMA foreign_keys=ON')
            conn.execute('PRAGMA journal_mode=WAL')
    return engine, sessionmaker(engine, expire_on_commit=False)


def initialize(engine):
    Base.metadata.create_all(engine)
    # Add new columns to earlier installations without dropping existing users or history.
    additions = {
        'users': {'display_name': "VARCHAR(80) NOT NULL DEFAULT '学习者'", 'last_login': 'DATETIME NULL'},
        'sessions': {'status': "VARCHAR(20) NOT NULL DEFAULT 'ongoing'", 'end_report': 'TEXT NULL', 'script_snapshot': 'JSON NULL', 'updated_at': 'DATETIME NULL', 'evidence_used': 'JSON NULL', 'events': 'JSON NULL', 'reflection': 'TEXT NULL', 'report_data': 'JSON NULL', 'is_busy': 'BOOLEAN NOT NULL DEFAULT 0', 'busy_at': 'DATETIME NULL'},
    }
    with engine.begin() as conn:
        for table, columns in additions.items():
            existing = {c['name'] for c in inspect(conn).get_columns(table)}
            for name, ddl in columns.items():
                if name not in existing:
                    conn.execute(text(f'ALTER TABLE {table} ADD COLUMN {name} {ddl}'))
