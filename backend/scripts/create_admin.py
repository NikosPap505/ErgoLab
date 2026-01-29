import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from passlib.context import CryptContext

from app.core.database import SessionLocal
from app.models.user import User, UserRole

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


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
            hashed_password=pwd_context.hash("admin123"),
            full_name="Administrator",
            phone="+30 210 1234567",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db.add(admin)
        db.commit()
        print("✅ Admin user created successfully!")
        print("   Email: admin@ergolab.gr")
        print("   Password: admin123")
        print("   ⚠️  Change password in production!")
    except Exception as exc:
        print(f"❌ Error creating admin: {exc}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_admin()
