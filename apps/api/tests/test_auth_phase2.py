import unittest
import uuid
from unittest.mock import AsyncMock, patch

from httpx import ASGITransport, AsyncClient

from app.api.deps import get_db
from app.core import security
from app.main import app
from app.models import User


class FakeRedis:
    def __init__(self) -> None:
        self.store: dict[str, str] = {}

    async def set(self, key: str, value: str, ex: int | None = None) -> bool:
        self.store[key] = value
        return True

    async def get(self, key: str) -> str | None:
        return self.store.get(key)


class AuthPhase2Tests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.user = User(
            id=uuid.uuid4(),
            email="user2@example.com",
            hashed_password="hashed",
            role_id=uuid.uuid4(),
            is_active=True,
        )
        self.redis = FakeRedis()

        async def fake_get_db():
            yield object()

        app.dependency_overrides[get_db] = fake_get_db
        self.redis_patcher = patch(
            "app.services.auth_session_service.get_redis_client",
            return_value=self.redis,
        )
        self.redis_patcher.start()
        self.transport = ASGITransport(app=app)
        self.client = AsyncClient(transport=self.transport, base_url="http://testserver")

    async def asyncTearDown(self) -> None:
        app.dependency_overrides.clear()
        self.redis_patcher.stop()
        await self.client.aclose()

    async def test_login_returns_access_and_refresh_tokens_with_explicit_claim_types(self) -> None:
        with patch(
            "app.api.routes.auth.authenticate_user",
            new=AsyncMock(return_value=self.user),
        ):
            response = await self.client.post(
                "/auth/login",
                json={"email": self.user.email, "password": "Passw0rd!"},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["token_type"], security.BEARER_TOKEN_TYPE)
        access_claims = security.decode_token_claims(
            payload["access_token"],
            expected_type=security.ACCESS_TOKEN_KIND,
        )
        refresh_claims = security.decode_token_claims(
            payload["refresh_token"],
            expected_type=security.REFRESH_TOKEN_KIND,
        )
        self.assertEqual(access_claims.sub, str(self.user.id))
        self.assertEqual(refresh_claims.sub, str(self.user.id))
        self.assertIsNotNone(refresh_claims.sid)
        self.assertIsNotNone(refresh_claims.jti)

    async def test_refresh_rotates_refresh_token_and_revokes_old_token(self) -> None:
        with patch(
            "app.api.routes.auth.authenticate_user",
            new=AsyncMock(return_value=self.user),
        ), patch(
            "app.services.auth_session_service.get_active_user_by_id",
            new=AsyncMock(return_value=self.user),
        ):
            login_response = await self.client.post(
                "/auth/login",
                json={"email": self.user.email, "password": "Passw0rd!"},
            )
            first_refresh_token = login_response.json()["refresh_token"]
            first_claims = security.decode_token_claims(
                first_refresh_token,
                expected_type=security.REFRESH_TOKEN_KIND,
            )

            refresh_response = await self.client.post(
                "/auth/refresh",
                json={"refresh_token": first_refresh_token},
            )

            self.assertEqual(refresh_response.status_code, 200)
            second_refresh_token = refresh_response.json()["refresh_token"]
            second_claims = security.decode_token_claims(
                second_refresh_token,
                expected_type=security.REFRESH_TOKEN_KIND,
            )

            self.assertEqual(first_claims.sid, second_claims.sid)
            self.assertNotEqual(first_claims.jti, second_claims.jti)

            replay_response = await self.client.post(
                "/auth/refresh",
                json={"refresh_token": first_refresh_token},
            )

        self.assertEqual(replay_response.status_code, 401)
        self.assertEqual(
            replay_response.json()["detail"],
            "Refresh token has been revoked",
        )

    async def test_refresh_accepts_legacy_query_param(self) -> None:
        with patch(
            "app.api.routes.auth.authenticate_user",
            new=AsyncMock(return_value=self.user),
        ), patch(
            "app.services.auth_session_service.get_active_user_by_id",
            new=AsyncMock(return_value=self.user),
        ):
            login_response = await self.client.post(
                "/auth/login",
                json={"email": self.user.email, "password": "Passw0rd!"},
            )
            refresh_token = login_response.json()["refresh_token"]

            response = await self.client.post(f"/auth/refresh?token={refresh_token}")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("access_token", payload)
        self.assertIn("refresh_token", payload)

    async def test_refresh_rejects_invalid_token(self) -> None:
        response = await self.client.post(
            "/auth/refresh",
            json={"refresh_token": "not-a-token"},
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Invalid refresh token")

    async def test_refresh_rejects_expired_token(self) -> None:
        with patch(
            "app.api.routes.auth.authenticate_user",
            new=AsyncMock(return_value=self.user),
        ), patch(
            "app.services.auth_session_service.get_active_user_by_id",
            new=AsyncMock(return_value=self.user),
        ):
            login_response = await self.client.post(
                "/auth/login",
                json={"email": self.user.email, "password": "Passw0rd!"},
            )
            refresh_token = login_response.json()["refresh_token"]
            refresh_claims = security.decode_token_claims(
                refresh_token,
                expected_type=security.REFRESH_TOKEN_KIND,
            )

            expired_refresh_token = security.create_refresh_token(
                str(self.user.id),
                session_id=refresh_claims.sid,
                token_id=refresh_claims.jti,
                expires_minutes=-1,
            )

            response = await self.client.post(
                "/auth/refresh",
                json={"refresh_token": expired_refresh_token},
            )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Refresh token expired")

    async def test_revoked_refresh_token_cannot_be_used_after_logout(self) -> None:
        with patch(
            "app.api.routes.auth.authenticate_user",
            new=AsyncMock(return_value=self.user),
        ), patch(
            "app.services.auth_session_service.get_active_user_by_id",
            new=AsyncMock(return_value=self.user),
        ):
            login_response = await self.client.post(
                "/auth/login",
                json={"email": self.user.email, "password": "Passw0rd!"},
            )
            refresh_token = login_response.json()["refresh_token"]

            logout_response = await self.client.post(
                "/auth/logout",
                json={"refresh_token": refresh_token},
            )
            refresh_response = await self.client.post(
                "/auth/refresh",
                json={"refresh_token": refresh_token},
            )

        self.assertEqual(logout_response.status_code, 204)
        self.assertEqual(refresh_response.status_code, 401)
        self.assertEqual(
            refresh_response.json()["detail"],
            "Refresh token has been revoked",
        )


if __name__ == "__main__":
    unittest.main()
