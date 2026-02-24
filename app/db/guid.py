"""
Platform-independent UUID type for SQLAlchemy ORM.

This module provides a custom GUID (Globally Unique Identifier) type that:
    - Uses PostgreSQL native UUID type for optimal storage and performance
    - Falls back to CHAR(32) for SQLite and other databases
    - Automatically converts between Python UUID objects and database representations
    - Handles both string and UUID object inputs transparently

Usage in models:
    >>> from sqlalchemy import Column
    >>> from app.db.guid import GUID
    >>> 
    >>> class User(Base):
    ...     __tablename__ = "users"
    ...     id: Mapped[UUID] = mapped_column(GUID, primary_key=True, default=uuid4)
"""

import uuid
from typing import Any, Optional, cast
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID as PG_UUID


class GUID(TypeDecorator):
    """
    Platform-independent GUID type for SQLAlchemy.
    
    Provides transparent UUID handling across different database backends:
    - PostgreSQL: Uses native UUID type (most efficient)
    - SQLite/Others: Uses CHAR(32) with hex string representation
    
    Automatically handles conversion between:
    - Python uuid.UUID objects
    - String representations (hex or UUID format)
    - Database-specific storage
    
    Examples:
        >>> from sqlalchemy import Column, String
        >>> from app.db.guid import GUID
        >>> id = Column(GUID, primary_key=True, default=uuid4)
        
        >>> # Python: use UUID objects
        >>> user.id = uuid.uuid4()
        >>> print(user.id)  # <UUID object>
        
        >>> # Database: automatically converted
        >>> # PostgreSQL: UUID type
        >>> # SQLite: CHAR(32) hex string
    """
    
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect: Any) -> Any:
        """
        Determine the appropriate column type for the given database dialect.
        
        Args:
            dialect: SQLAlchemy dialect (postgresql, sqlite, etc.)
        
        Returns:
            Dialect-specific type descriptor (UUID for PostgreSQL, CHAR(32) for others)
        """
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_UUID())
        else:
            return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value: Any, dialect: Any) -> Optional[str]:
        """
        Convert Python value to database value before INSERT/UPDATE.
        
        Args:
            value: Python uuid.UUID object or string, or None
            dialect: SQLAlchemy dialect
        
        Returns:
            Database-appropriate representation:
            - PostgreSQL: UUID string (e.g., "550e8400-e29b-41d4-a716-446655440000")
            - Others: 32-char hex string (e.g., "550e8400e29b41d4a716446655440000")
            - None: None
        """
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return "%.32x" % uuid.UUID(value).int
            else:
                return "%.32x" % value.int

    def process_result_value(self, value: Any, dialect: Any) -> Optional[uuid.UUID]:
        """
        Convert database value to Python value after SELECT.
        
        Args:
            value: Value from database (UUID string or hex string), or None
            dialect: SQLAlchemy dialect
        
        Returns:
            Python uuid.UUID object, or None
        """
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                value = uuid.UUID(value)
            return cast(uuid.UUID, value)
