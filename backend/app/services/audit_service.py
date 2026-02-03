from typing import Optional, Dict, Any
import hashlib
import hmac
import logging
import ipaddress

from sqlalchemy.orm import Session
from fastapi import Request

from app.core.config import settings
from app.models.audit import AuditLog
from app.models.user import User


class AuditService:
    @staticmethod
    def log_action(
        db: Session,
        user: User,
        action: str,
        table_name: str,
        record_id: Optional[int],
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None,
    ) -> AuditLog:
        """Create an audit log entry"""
        
        ip_address = None
        user_agent = None
        if request:
            # Handle IP extraction securely with config flag
            forwarded_for = request.headers.get("x-forwarded-for")
            extracted_ip = None
            
            if settings.TRUST_PROXY_HEADERS and forwarded_for:
                try:
                    # Parse first IP and validate format
                    candidate = forwarded_for.split(",")[0].strip()
                    ipaddress.ip_address(candidate)  # Raises ValueError if invalid
                    extracted_ip = candidate
                except ValueError:
                    logging.warning(f"Invalid X-Forwarded-For IP ignored: {forwarded_for}")
            
            # Fallback to direct connection IP if no trusted header or validation failed
            if not extracted_ip and request.client:
                extracted_ip = request.client.host
                
            ip_address = extracted_ip
            user_agent = request.headers.get("user-agent")
        
        # Hash email for privacy using HMAC to prevent precomputation
        email_hash = None
        if user.email:
            if not settings.EMAIL_HASH_KEY:
                logging.error("EMAIL_HASH_KEY is missing in configuration")
                raise ValueError("EMAIL_HASH_KEY configuration is required for audit logging")
            
            email_hash = hmac.new(
                settings.EMAIL_HASH_KEY.encode(), 
                user.email.lower().encode(), 
                hashlib.sha256
            ).hexdigest()

        audit_log = AuditLog(
            user_id=user.id,
            user_email_hash=email_hash,
            action=action,
            table_name=table_name,
            record_id=record_id,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        db.add(audit_log)
        db.commit()
        
        return audit_log
