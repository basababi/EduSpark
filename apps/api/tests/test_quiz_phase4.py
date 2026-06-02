import unittest
import uuid
from unittest.mock import AsyncMock, patch

from httpx import ASGITransport, AsyncClient

from app.api.deps import get_current_user, get_db
from app.main import app
from app.models import Role, User


class QuizPhase4Tests(unittest.IsolatedAsyncioTestCase):
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

    async def test_read_quizzes(self) -> None:
        expected = [
            {
                "id": str(uuid.uuid4()),
                "title": "Python Functions Check",
                "mode": "practice",
                "level": "beginner",
                "topic_id": str(uuid.uuid4()),
                "topic_title": "Functions",
                "subject_id": str(uuid.uuid4()),
                "subject_name": "Programming",
                "question_count": 10,
                "last_score": 80.0,
                "last_attempt_at": "2026-04-04T08:00:00Z",
            }
        ]
        with patch(
            "app.api.routes.quizzes.list_quizzes",
            new=AsyncMock(return_value=expected),
        ):
            response = await self.client.get("/quizzes")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected)

    async def test_read_quiz_detail(self) -> None:
        quiz_id = str(uuid.uuid4())
        expected = {
            "id": quiz_id,
            "title": "Linear Equations Quick Check",
            "mode": "practice",
            "level": "intermediate",
            "topic_id": str(uuid.uuid4()),
            "topic_title": "Linear equations",
            "subject_id": str(uuid.uuid4()),
            "subject_name": "Mathematics",
            "question_count": 1,
            "last_score": None,
            "last_attempt_at": None,
            "questions": [
                {
                    "id": str(uuid.uuid4()),
                    "question_text": "Solve 2x + 4 = 10",
                    "choices": {"A": "2", "B": "3"},
                    "explanation": "x = 3",
                }
            ],
        }
        with patch(
            "app.api.routes.quizzes.get_quiz_detail",
            new=AsyncMock(return_value=expected),
        ):
            response = await self.client.get(f"/quizzes/{quiz_id}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected)

    async def test_create_quiz_attempt(self) -> None:
        quiz_id = str(uuid.uuid4())
        question_id = str(uuid.uuid4())
        expected = {
            "attempt_id": str(uuid.uuid4()),
            "quiz_id": quiz_id,
            "score": 100.0,
            "correct_count": 1,
            "total_questions": 1,
            "completed_at": "2026-04-04T08:00:00Z",
            "answers": [
                {
                    "question_id": question_id,
                    "selected_answer": "B",
                    "correct_answer": "B",
                    "is_correct": True,
                    "explanation": "x = 3",
                }
            ],
        }
        with patch(
            "app.api.routes.quizzes.submit_quiz_attempt",
            new=AsyncMock(return_value=expected),
        ):
            response = await self.client.post(
                f"/quizzes/{quiz_id}/attempts",
                json={"answers": [{"question_id": question_id, "selected_answer": "B"}]},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected)

    async def test_read_quiz_attempt_history(self) -> None:
        expected = [
            {
                "attempt_id": str(uuid.uuid4()),
                "quiz_id": str(uuid.uuid4()),
                "quiz_title": "Newton Motion Basics",
                "subject_name": "Physics",
                "score": 75.0,
                "correct_count": 3,
                "total_questions": 4,
                "completed_at": "2026-04-04T08:00:00Z",
            }
        ]
        with patch(
            "app.api.routes.quizzes.get_quiz_attempt_history",
            new=AsyncMock(return_value=expected),
        ):
            response = await self.client.get("/quizzes/attempts/history")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected)


if __name__ == "__main__":
    unittest.main()
