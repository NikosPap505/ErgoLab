import logging
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
import time

from app.core.config import settings

logger = logging.getLogger(__name__)

# Create engine with optimized settings
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=False,  # Set to True for SQL debugging
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# Query performance logging
@event.listens_for(engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Track query start time"""
    conn.info.setdefault('query_start_time', []).append(time.time())


@event.listens_for(engine, "after_cursor_execute")  
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Log slow queries (>100ms)"""
    start_times = conn.info.get('query_start_time', [])
    if start_times:
        total = time.time() - start_times.pop(-1)
        if total > 0.1:  # Log queries > 100ms
            clean_statement = ' '.join(statement.split())[:200]
            logger.warning(f"Slow query ({total:.3f}s): {clean_statement}")


def get_db():
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
