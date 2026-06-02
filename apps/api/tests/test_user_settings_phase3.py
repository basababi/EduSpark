import unittest
import uuid
from unittest.mock import AsyncMock, patch

from httpx import ASGITransport, AsyncClient

from app.api.deps import get_current_user, get_db
from app.main import app
from app.models import Role, User


class UserSettingsPhase3Tests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.user = User(
            id=uuid.uuid4(),
            email="user2@example.com",
            hashed_password="hashed",
            role_id=uuid.uuid4(),
            is_active=True,
        )
        self.user.role = Role(id=uuid.uuid4(), name="admin", description="admin")

        async def fake_get_db():
            yield object()

        async def fake_get_current_user():
            return self.user

        app.dependency_overrides[get_db] = fake_get_db
        app.dependency_overrides[get_current_user] = fake_get_current_user
        self.transport = ASGITransport(app=app)
        self.client = AsyncClient(transport=self.transport, base_url="http://testserver")

    async def asyncTearDown(self) -> None:
        app.dependency_overrides.clear()
        await self.client.aclose()

    async def test_get_my_profile(self) -> None:
        expected_payload = {
            "name": "User Two",
            "email": "user2@example.com",
            "role": "admin",
            "track": "intermediate",
            "interests": ["Math", "Physics"],
            "avatar_url": None,
            "locale": "mn",
            "timezone": "Asia/Ulaanbaatar",
        }
        with patch(
            "app.api.routes.users.get_my_profile",
            new=AsyncMock(return_value=expected_payload),
        ):
            response = await self.client.get("/users/me/profile")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_payload)

    async def test_patch_my_profile(self) -> None:
        expected_payload = {
            "name": "Updated User",
            "email": "updated@example.com",
            "role": "admin",
            "track": "advanced",
            "interests": ["Math", "Programming"],
            "avatar_url": None,
            "locale": "mn",
            "timezone": "Asia/Ulaanbaatar",
        }
        with patch(
            "app.api.routes.users.update_my_profile",
            new=AsyncMock(return_value=expected_payload),
        ):
            response = await self.client.patch(
                "/users/me/profile",
                json={
                    "name": "Updated User",
                    "email": "updated@example.com",
                    "track": "advanced",
                    "interests": ["Math", "Programming"],
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_payload)

    async def test_get_my_preferences(self) -> None:
        expected_payload = {
            "email_notifications": True,
            "weekly_report": False,
            "daily_reminder": True,
            "dark_mode": False,
            "compact_view": False,
        }
        with patch(
            "app.api.routes.users.get_my_preferences",
            new=AsyncMock(return_value=expected_payload),
        ):
            response = await self.client.get("/users/me/preferences")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_payload)

    async def test_patch_my_preferences(self) -> None:
        expected_payload = {
            "email_notifications": False,
            "weekly_report": True,
            "daily_reminder": False,
            "dark_mode": True,
            "compact_view": True,
        }
        with patch(
            "app.api.routes.users.update_my_preferences",
            new=AsyncMock(return_value=expected_payload),
        ):
            response = await self.client.patch(
                "/users/me/preferences",
                json={
                    "email_notifications": False,
                    "weekly_report": True,
                    "daily_reminder": False,
                    "dark_mode": True,
                    "compact_view": True,
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_payload)


if __name__ == "__main__":
    unittest.main()
