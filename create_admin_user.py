#!/usr/bin/env python3
"""
Script to create an admin user for testing Axis AI.
Usage: python create_admin_user.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from core.database import get_db, User, SessionLocal
from core.security.auth import get_password_hash
from datetime import datetime

def create_admin_user():
    """Create admin user with credentials: admin/1609"""
    db = SessionLocal()
    
    try:
        # Check if admin user already exists
        existing_user = db.query(User).filter(User.username == "admin").first()
        if existing_user:
            print("Admin user already exists!")
            print(f"Username: {existing_user.username}")
            print(f"Email: {existing_user.email}")
            print(f"Is Admin: {existing_user.is_admin}")
            print(f"Is Active: {existing_user.is_active}")
            return
        
        # Create admin user
        hashed_password = get_password_hash("1609")
        
        admin_user = User(
            username="admin",
            email="admin@axis.local",
            hashed_password=hashed_password,
            is_admin=True,
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print("✅ Admin user created successfully!")
        print(f"Username: admin")
        print(f"Password: 1609")
        print(f"Email: admin@axis.local")
        print(f"User ID: {admin_user.id}")
        print(f"Is Admin: {admin_user.is_admin}")
        print("")
        print("🚀 You can now login at: http://localhost:8000")
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_admin_user() 