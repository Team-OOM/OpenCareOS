"""
OpenCareOS - User Repository
Apache License 2.0
"""

from typing import Optional, List
from uuid import UUID
from beanie import PydanticObjectId
from pymongo import ASCENDING, DESCENDING
from app.models.user import User, UserRole, UserStatus
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """User repository with specialized queries."""

    def __init__(self):
        super().__init__(User)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return await self.model.find_one({"email": email.lower(), "is_deleted": {"$ne": True}})

    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        return await self.model.find_one({"username": username, "is_deleted": {"$ne": True}})

    async def get_by_email_or_username(self, identifier: str) -> Optional[User]:
        """Get user by email or username."""
        return await self.model.find_one({
            "$or": [
                {"email": identifier.lower()},
                {"username": identifier},
            ],
            "is_deleted": {"$ne": True},
        })

    async def get_by_role(self, role: UserRole, params) -> List[User]:
        """Get users by role with pagination."""
        filters = {"role": role, "is_deleted": {"$ne": True}}
        return await self.list(params, filters=filters)

    async def get_active_users(self, params) -> List[User]:
        """Get active users with pagination."""
        filters = {"status": UserStatus.ACTIVE, "is_deleted": {"$ne": True}}
        return await self.list(params, filters=filters)

    async def get_doctors(self, params) -> List[User]:
        """Get all doctors with pagination."""
        filters = {"role": UserRole.DOCTOR, "is_deleted": {"$ne": True}}
        return await self.list(params, filters=filters)

    async def get_patients(self, params) -> List[User]:
        """Get all patients with pagination."""
        filters = {"role": UserRole.PATIENT, "is_deleted": {"$ne": True}}
        return await self.list(params, filters=filters)

    async def search(self, query: str, params) -> List[User]:
        """Search users by name, email, or username."""
        filters = {
            "$or": [
                {"full_name": {"$regex": query, "$options": "i"}},
                {"email": {"$regex": query, "$options": "i"}},
                {"username": {"$regex": query, "$options": "i"}},
            ],
            "is_deleted": {"$ne": True},
        }
        return await self.list(params, filters=filters)

    async def email_exists(self, email: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if email exists."""
        query = {"email": email.lower(), "is_deleted": {"$ne": True}}
        if exclude_id:
            query["_id"] = {"$ne": exclude_id}
        return await self.exists(query)

    async def username_exists(self, username: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if username exists."""
        query = {"username": username, "is_deleted": {"$ne": True}}
        if exclude_id:
            query["_id"] = {"$ne": exclude_id}
        return await self.exists(query)

    async def get_users_with_tokens(self, token: str) -> Optional[User]:
        """Get user by refresh token."""
        return await self.model.find_one({"refresh_tokens": token, "is_deleted": {"$ne": True}})

    async def add_refresh_token(self, user_id: UUID, token: str) -> None:
        """Add refresh token to user."""
        user = await self.get_by_id(user_id)
        if user:
            user.add_refresh_token(token)
            await user.save()

    async def remove_refresh_token(self, user_id: UUID, token: str) -> None:
        """Remove refresh token from user."""
        user = await self.get_by_id(user_id)
        if user:
            user.remove_refresh_token(token)
            await user.save()

    async def revoke_all_tokens(self, user_id: UUID) -> None:
        """Revoke all refresh tokens for user."""
        user = await self.get_by_id(user_id)
        if user:
            user.revoke_all_tokens()
            await user.save()

    async def get_staff_users(self, params) -> List[User]:
        """Get all staff users (doctors, nurses, admin)."""
        filters = {
            "role": {"$in": [UserRole.DOCTOR, UserRole.NURSE, UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.ADMIN_STAFF]},
            "is_deleted": {"$ne": True},
        }
        return await self.list(params, filters=filters)