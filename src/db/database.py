"""
Database connection and session management
"""

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from src.core.config import settings

# Create async engine for PostgreSQL
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
    poolclass=NullPool if "test" in settings.DATABASE_URL else None,
    pool_pre_ping=True,
    pool_recycle=300,
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base model class
Base = declarative_base()

# Convention for naming constraints
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

Base.metadata = MetaData(naming_convention=convention)


def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def set_tenant_context(db_session, tenant_id: str):
    """Set tenant context for row-level security"""
    db_session.execute(f"SELECT set_config('app.current_tenant_id', '{tenant_id}', false)")


def get_current_tenant_id(db_session) -> str:
    """Get current tenant ID from session"""
    result = db_session.execute("SELECT current_setting('app.current_tenant_id', true)")
    return result.scalar()