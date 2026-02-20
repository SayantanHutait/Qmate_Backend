"""
Script to seed initial data (departments, admin user).
Run after migrations: python scripts/seed_data.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import Department, User, UserRole
from app.core.security import get_password_hash


def seed_departments(db: Session):
    """Seed default departments."""
    departments = [
        {"name": "Computer Science", "slug": "cs", "description": "Computer Science Department"},
        {"name": "Administration", "slug": "admin", "description": "General Administration"},
        {"name": "Finance", "slug": "finance", "description": "Finance and Fees Department"},
        {"name": "Academic Affairs", "slug": "academic", "description": "Academic Affairs Department"},
    ]
    
    for dept_data in departments:
        existing = db.query(Department).filter(Department.slug == dept_data["slug"]).first()
        if not existing:
            department = Department(**dept_data)
            db.add(department)
            print(f"Created department: {dept_data['name']}")
    
    db.commit()


def seed_admin_user(db: Session):
    """Seed default admin user."""
    admin_email = "admin@qmate.edu"
    admin_password = "admin123"  # Change in production!
    
    existing = db.query(User).filter(User.email == admin_email).first()
    if not existing:
        admin = User(
            email=admin_email,
            password_hash=get_password_hash(admin_password),
            name="System Administrator",
            role=UserRole.ADMIN,
        )
        db.add(admin)
        db.commit()
        print(f"Created admin user: {admin_email} (password: {admin_password})")
    else:
        print(f"Admin user already exists: {admin_email}")


def main():
    """Main seeding function."""
    db = SessionLocal()
    try:
        print("Seeding departments...")
        seed_departments(db)
        
        print("\nSeeding admin user...")
        seed_admin_user(db)
        
        print("\n✅ Seeding completed!")
    except Exception as e:
        print(f"\n❌ Error seeding data: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
