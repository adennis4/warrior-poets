#!/usr/bin/env python3
"""
Database models and helpers for user authentication and Kalshi credentials.
Uses SQLAlchemy with PostgreSQL.
"""

import os
import secrets
from datetime import datetime, timedelta
from contextlib import contextmanager

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

from encryption import encrypt_credential, decrypt_credential

DATABASE_URL = os.environ.get('DATABASE_URL', '')

# Handle Render's postgres:// vs postgresql:// URL format
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

Base = declarative_base()

# Create engine lazily to avoid connection issues at import time
_engine = None
_SessionLocal = None


def get_engine():
    """Get or create the database engine."""
    global _engine
    if _engine is None:
        if not DATABASE_URL:
            raise ValueError("DATABASE_URL environment variable not set")
        _engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    return _engine


def get_session_factory():
    """Get or create the session factory."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine())
    return _SessionLocal


@contextmanager
def get_db():
    """Context manager for database sessions."""
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


class User(Base):
    """User account linked to Yahoo identity."""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    yahoo_guid = Column(String(255), unique=True, nullable=False)
    yahoo_email = Column(String(255))
    yahoo_name = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    kalshi_credentials = relationship("KalshiCredentials", back_populates="user", uselist=False)
    sessions = relationship("Session", back_populates="user")


class KalshiCredentials(Base):
    """Encrypted Kalshi API credentials for a user."""
    __tablename__ = 'kalshi_credentials'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), unique=True)
    encrypted_api_key = Column(Text, nullable=False)
    encrypted_private_key = Column(Text, nullable=False)
    encryption_iv = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    user = relationship("User", back_populates="kalshi_credentials")


class Session(Base):
    """User session for authentication."""
    __tablename__ = 'sessions'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    session_token = Column(String(255), unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    user = relationship("User", back_populates="sessions")


def init_db():
    """Create all database tables."""
    Base.metadata.create_all(get_engine())


def get_or_create_user(yahoo_guid: str, yahoo_email: str = None, yahoo_name: str = None) -> User:
    """Get existing user or create new one from Yahoo info."""
    with get_db() as db:
        user = db.query(User).filter(User.yahoo_guid == yahoo_guid).first()
        if user:
            # Update name/email if provided
            if yahoo_email:
                user.yahoo_email = yahoo_email
            if yahoo_name:
                user.yahoo_name = yahoo_name
            db.commit()
            db.refresh(user)
            return user

        # Create new user
        user = User(
            yahoo_guid=yahoo_guid,
            yahoo_email=yahoo_email,
            yahoo_name=yahoo_name
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user


def create_session(user_id: int, expires_days: int = 30) -> str:
    """Create a new session for a user, returns session token."""
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(days=expires_days)

    with get_db() as db:
        session = Session(
            user_id=user_id,
            session_token=token,
            expires_at=expires_at
        )
        db.add(session)
        db.commit()

    return token


def get_user_by_session(session_token: str) -> User | None:
    """Get user from session token, returns None if invalid/expired."""
    with get_db() as db:
        session = db.query(Session).filter(
            Session.session_token == session_token,
            Session.expires_at > datetime.utcnow()
        ).first()

        if not session:
            return None

        user = db.query(User).filter(User.id == session.user_id).first()
        return user


def delete_session(session_token: str):
    """Delete a session (logout)."""
    with get_db() as db:
        db.query(Session).filter(Session.session_token == session_token).delete()
        db.commit()


def save_kalshi_credentials(user_id: int, api_key: str, private_key: str):
    """Encrypt and save Kalshi credentials for a user."""
    # Encrypt both credentials with the same IV (they're stored together)
    encrypted_api_key, iv = encrypt_credential(api_key)
    encrypted_private_key, _ = encrypt_credential(private_key)

    with get_db() as db:
        # Delete existing credentials if any
        db.query(KalshiCredentials).filter(KalshiCredentials.user_id == user_id).delete()

        # Save new credentials
        creds = KalshiCredentials(
            user_id=user_id,
            encrypted_api_key=encrypted_api_key,
            encrypted_private_key=encrypted_private_key,
            encryption_iv=iv
        )
        db.add(creds)
        db.commit()


def get_kalshi_credentials(user_id: int) -> tuple[str, str] | None:
    """Get decrypted Kalshi credentials for a user."""
    with get_db() as db:
        creds = db.query(KalshiCredentials).filter(
            KalshiCredentials.user_id == user_id
        ).first()

        if not creds:
            return None

        api_key = decrypt_credential(creds.encrypted_api_key, creds.encryption_iv)
        private_key = decrypt_credential(creds.encrypted_private_key, creds.encryption_iv)
        return api_key, private_key


def delete_kalshi_credentials(user_id: int):
    """Delete Kalshi credentials for a user."""
    with get_db() as db:
        db.query(KalshiCredentials).filter(KalshiCredentials.user_id == user_id).delete()
        db.commit()


def user_has_kalshi_credentials(user_id: int) -> bool:
    """Check if user has linked Kalshi credentials."""
    with get_db() as db:
        count = db.query(KalshiCredentials).filter(
            KalshiCredentials.user_id == user_id
        ).count()
        return count > 0


def cleanup_expired_sessions():
    """Delete all expired sessions (call periodically)."""
    with get_db() as db:
        db.query(Session).filter(Session.expires_at < datetime.utcnow()).delete()
        db.commit()
