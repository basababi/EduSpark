import unittest
import uuid
from unittest.mock import AsyncMock, patch

from httpx import ASGITransport, AsyncClient

from app.api.deps import get_current_user, get_db
from app.main import app
from app.models import Role, User


class ProgressPhase4Tests(unittest.IsolatedAsyncioTestCase):
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

    async def test_read_progress_summary(self) -> None:
        expected = {
            "weekly_minutes": 990,
            "weekly_hours": 16.5,
            "weekly_goal_minutes": 1320,
            "weekly_goal_percent": 75.0,
            "average_quiz_score": 85.0,
            "completed_quizzes": 48,
            "completed_lessons": 48,
            "subject_progress": [
                {
                    "subject_id": str(uuid.uuid4()),
                    "subject_name": "Mathematics",
                    "progress_percent": 82.5,
                    "average_quiz_score": 88.0,
                    "study_minutes": 300,
                    "completed_quizzes": 20,
                }
            ],
            "weekly_trend": [{"date": "2026-04-04", "minutes": 120}],
        }
        with patch(
            "app.api.routes.progress.get_progress_summary",
            new=AsyncMock(return_value=expected),
        ):
            response = await self.client.get("/progress/summary")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected)

    async def test_create_study_session(self) -> None:
        expected = {
            "id": str(uuid.uuid4()),
            "subject_id": str(uuid.uuid4()),
            "duration_minutes": 45,
            "studied_at": "2026-04-04T08:00:00Z",
        }
        with patch(
            "app.api.routes.progress.record_study_session",
            new=AsyncMock(return_value=expected),
        ):
            response = await self.client.post(
                "/progress/study-sessions",
                json={
                    "subject_id": expected["subject_id"],
                    "duration_minutes": 45,
                },
            )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json(), expected)

    async def test_read_progress_snapshots(self) -> None:
        expected = [
            {
                "id": str(uuid.uuid4()),
                "subject_id": str(uuid.uuid4()),
                "metric": {"event": "quiz_attempt_submitted", "score": 90},
                "captured_at": "2026-04-04T08:00:00Z",
            }
        ]
        with patch(
            "app.api.routes.progress.get_progress_snapshots",
            new=AsyncMock(return_value=expected),
        ):
            response = await self.client.get("/progress/snapshots")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected)


if __name__ == "__main__":
    unittest.main()
