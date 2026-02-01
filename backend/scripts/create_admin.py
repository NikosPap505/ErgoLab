import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from passlib.context import CryptContext

from app.core.database import SessionLocal
from app.models.user import User, UserRole

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Read admin password from environment variable for security
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")


def create_admin():
    db = SessionLocal()

    try:
        admin = db.query(User).filter(User.email == "admin@ergolab.gr").first()
        if admin:
            print("✓ Admin user already exists")
            return

        admin = User(
            email="admin@ergolab.gr",
            username="admin",
            hashed_password=pwd_context.hash(ADMIN_PASSWORD),
            full_name="Administrator",
            phone="+30 210 1234567",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db.add(admin)
        db.commit()
        print("✅ Admin user created successfully!")
        print("   Email: admin@ergolab.gr")
        if ADMIN_PASSWORD == "admin123":
            print("   Password: admin123 (default)")
            print("   ⚠️  SECURITY WARNING: Set ADMIN_PASSWORD environment variable in production!")
        else:
            print("   Password: Set from ADMIN_PASSWORD environment variable")
    except Exception as exc:
        print(f"❌ Error creating admin: {exc}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_admin()
