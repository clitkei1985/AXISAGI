from fastapi import Depends, HTTPException, status
from core.database import User
from .auth import get_current_active_user

class RoleChecker:
    def __init__(self, required_roles: list):
        self.required_roles = required_roles
    
    def __call__(self, user: User = Depends(get_current_active_user)):
        for role in self.required_roles:
            if not hasattr(user, role) or not getattr(user, role):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role {role} required"
                )
        return user

# Usage example:
# require_admin = RoleChecker(["is_admin"])
# @app.get("/admin", dependencies=[Depends(require_admin)]) 