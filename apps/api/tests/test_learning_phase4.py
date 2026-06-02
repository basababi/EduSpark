import unittest
import uuid
from unittest.mock import AsyncMock, patch

from httpx import ASGITransport, AsyncClient

from app.api.deps import get_current_user, get_db
from app.main import app
from app.models import Role, User


class LearningPhase4Tests(unittest.IsolatedAsyncioTestCase):
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

    async def test_read_subjects(self) -> None:
        subject_id = str(uuid.uuid4())
        expected = [
            {
                "id": subject_id,
                "name": "Mathematics",
                "description": "Core math track",
                "difficulty_level": "intermediate",
                "modules_count": 3,
                "topics_count": 12,
                "lessons_count": 38,
                "progress_percent": 84.5,
            }
        ]
        with patch(
            "app.api.routes.learning.list_subjects",
            new=AsyncMock(return_value=expected),
        ):
            response = await self.client.get("/subjects")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected)

    async def test_read_subject_detail(self) -> None:
        subject_id = str(uuid.uuid4())
        module_id = str(uuid.uuid4())
        topic_id = str(uuid.uuid4())
        lesson_id = str(uuid.uuid4())
        expected = {
            "id": subject_id,
            "name": "Programming",
            "description": "Backend learning track",
            "difficulty_level": "beginner",
            "modules_count": 1,
            "topics_count": 1,
            "lessons_count": 1,
            "progress_percent": 65.0,
            "modules": [
                {
                    "id": module_id,
                    "title": "Python Basics",
                    "description": "Starter module",
                    "order": 1,
                    "topics": [
                        {
                            "id": topic_id,
                            "title": "Functions",
                            "objective": "Learn function basics",
                            "difficulty": "beginner",
                            "lessons": [
                                {
                                    "id": lesson_id,
                                    "title": "Def and Return",
                                    "summary": "Function declaration",
                                }
                            ],
                        }
                    ],
                }
            ],
        }
        with patch(
            "app.api.routes.learning.get_subject_detail",
            new=AsyncMock(return_value=expected),
        ):
            response = await self.client.get(f"/subjects/{subject_id}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected)

    async def test_read_lesson_detail(self) -> None:
        lesson_id = str(uuid.uuid4())
        expected = {
            "id": lesson_id,
            "title": "Linear equations",
            "summary": "Solve ax+b=0",
            "subject_id": str(uuid.uuid4()),
            "subject_name": "Mathematics",
            "module_id": str(uuid.uuid4()),
            "module_title": "Algebra",
            "topic_id": str(uuid.uuid4()),
            "topic_title": "Linear equations",
            "contents": [
                {
                    "id": str(uuid.uuid4()),
                    "content_type": "text",
                    "text_content": "Example lesson text",
                    "source": "lesson",
                    "language": "mn",
                }
            ],
        }
        with patch(
            "app.api.routes.learning.get_lesson_detail",
            new=AsyncMock(return_value=expected),
        ):
            response = await self.client.get(f"/lessons/{lesson_id}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected)


if __name__ == "__main__":
    unittest.main()
