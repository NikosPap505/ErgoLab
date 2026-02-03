from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from sqlalchemy.orm import relationship

from app.core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)  # Who made the change
    user_email_hash = Column(String, index=True)  # Masked identity
    action = Column(String, nullable=False)  # CREATE, UPDATE, DELETE
    table_name = Column(String, nullable=False, index=True)  # Which table
    record_id = Column(Integer)  # Which record
    old_values = Column(JSON)  # Previous state
    new_values = Column(JSON)  # New state
    ip_address = Column(String)
    user_agent = Column(String)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    def __repr__(self):
        return f"<AuditLog {self.action} on {self.table_name}:{self.record_id} by {self.user_email_hash}>"
