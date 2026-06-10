#!/usr/bin/env python3
"""Script to reset admin password."""
import os
import sys

# Add the app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.core.security import security
from app.models.user import User, Role


def reset_admin_password(new_password: str = "ChangeMe123!"):
    """Reset the admin user password."""
    db = SessionLocal()
    try:
        # Find admin user
        admin = db.query(User).filter(User.email == "admin@passwordmanager.local").first()
        
        if admin:
            admin.hashed_password = security.hash_password(new_password)
            db.commit()
            print(f"Admin password reset successfully!")
            print(f"Email: admin@passwordmanager.local")
            print(f"Password: {new_password}")
        else:
            print("Admin user not found. Creating new admin user...")
            
            # Check if roles exist
            if db.query(Role).count() == 0:
                # Create default roles
                roles = [
                    Role(name="Admin", description="Full system access", permissions="all"),
                    Role(name="Manager", description="Manage vaults and users", permissions="vault:create,vault:manage,user:read"),
                    Role(name="User", description="Basic user access", permissions="vault:read,credential:read"),
                ]
                for role in roles:
                    db.add(role)
                db.commit()
            
            # Create admin
            admin = User(
                email="admin@passwordmanager.local",
                username="admin",
                full_name="System Administrator",
                hashed_password=security.hash_password(new_password),
                role_id=1,
                is_superuser=True
            )
            db.add(admin)
            db.commit()
            print(f"Admin user created successfully!")
            print(f"Email: admin@passwordmanager.local")
            print(f"Password: {new_password}")
            
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    # Get password from command line or use default
    password = sys.argv[1] if len(sys.argv) > 1 else "ChangeMe123!"
    reset_admin_password(password)