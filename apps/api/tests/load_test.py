from locust import HttpUser, task, between, events
from random import choice, randint
import json

class EduSparkUser(HttpUser):
    wait_time = between(2, 5)

    def on_start(self):
        """Authenticate before running tasks."""
        resp = self.client.post("/auth/login", json={
            "email": f"user{randint(1, 100)}@example.mn",
            "password": "password123",
        })
        if resp.status_code == 200:
            self.access_token = resp.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.access_token}"}
        else:
            self.headers = {}

    @task(10)
    def learning_flow(self):
        """Flow: Fetch subjects → view lesson."""
        self.client.get("/subjects", headers=self.headers)

        subject_id = choice(["subj-1", "subj-2", "subj-3"])
        resp = self.client.get(f"/subjects/{subject_id}", headers=self.headers)

        if resp.status_code == 200:
            lesson_id = "lesson-1"
            self.client.get(f"/lessons/{lesson_id}", headers=self.headers)

    @task(5)
    def quiz_flow(self):
        """Flow: Get quizzes → attempt quiz."""
        resp = self.client.get("/quizzes", headers=self.headers)

        if resp.status_code == 200 and resp.json():
            quiz = resp.json()[0]
            quiz_id = quiz["id"]

            self.client.get(f"/quizzes/{quiz_id}", headers=self.headers)
            self.client.post(
                f"/quizzes/{quiz_id}/attempts",
                json={"answers": []},
                headers=self.headers
            )

    @task(3)
    def chat_flow(self):
        """Flow: Create session → send message."""
        resp = self.client.post("/chat/sessions", headers=self.headers)
        if resp.status_code == 200:
            session_id = resp.json()["session_id"]

            self.client.post(
                f"/chat/sessions/{session_id}/messages",
                json={"content": "How do I solve quadratic equations?"},
                headers=self.headers,
            )

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print("Load test started")

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print(f"\nTest completed.")
    print(f"Total requests: {environment.stats.total.num_requests}")
    print(f"Failed: {environment.stats.total.num_failures}")
    print(f"Avg response time: {environment.stats.total.avg_response_time:.0f}ms")
    print(f"p95 response time: {environment.stats.total.get_response_time_percentile(0.95):.0f}ms")
