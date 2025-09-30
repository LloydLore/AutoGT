"""Base model configuration for AutoGT TARA platform."""

from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.types import TypeDecorator, CHAR


class GUID(TypeDecorator):
    """Platform-independent GUID type.
    
    Uses PostgreSQL's UUID type when available, otherwise CHAR(32).
    """
    
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_UUID())
        else:
            return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, UUID):
                return "%.32x" % UUID(value).int
            else:
                return "%.32x" % value.int

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, UUID):
                return UUID(value)
            return value


class Base(DeclarativeBase):
    """Base class for all database models."""
    
    type_annotation_map = {
        UUID: GUID,
    }


class AuditMixin:
    """Mixin for audit timestamp fields."""
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )


class ISO21434Mixin:
    """Mixin for ISO/SAE 21434 compliance tracking."""
    
    iso_section: Mapped[str] = mapped_column(
        String(100),
        nullable=True,
        comment="ISO/SAE 21434 section reference"
    )
    compliance_notes: Mapped[str] = mapped_column(
        String(500),
        nullable=True,
        comment="Additional compliance documentation"
    )


class BaseModel(Base, AuditMixin):
    """Base model with UUID primary key and audit fields."""
    
    __abstract__ = True
    
    id: Mapped[UUID] = mapped_column(
        GUID,
        primary_key=True,
        default=uuid4,
        nullable=False
    )