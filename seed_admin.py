import os
import sys

# Add backend directory to sys path so we can import from backend module
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from backend.core.database import SessionLocal, engine
from backend.models.entities import Base, User
from backend.core.security import hash_password

def seed_super_admin():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "admin@reserve.ai").first()
        if not user:
            user = User(
                email="admin@reserve.ai",
                hashed_password=hash_password("admin123"),
                full_name="System Admin",
                role="SUPER_ADMIN",
                is_active=True
            )
            db.add(user)
            db.commit()
            print("Super Admin user created: admin@reserve.ai / admin123")
        else:
            print("Super Admin user already exists: admin@reserve.ai / admin123")
    finally:
        db.close()

if __name__ == "__main__":
    seed_super_admin()
