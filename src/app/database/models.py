"""SQLAlchemy metadata for Alembic migrations."""

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Index,
    MetaData,
    String,
    Table,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID

metadata = MetaData()

users = Table(
    "users",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")),
    Column("email", String(255), unique=True, nullable=False),
    Column("password_hash", String(255), nullable=False),
    Column("is_active", Boolean, server_default=text("false"), nullable=False),
    Column("activation_code", String(4), nullable=True),
    Column("activation_code_expires_at", DateTime(timezone=True), nullable=True),
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
    Column("updated_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
    Index("idx_users_email_lower", func.lower(Column("email"))),
)
