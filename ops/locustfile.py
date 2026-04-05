import itertools
import os
import random
import time

from locust import FastHttpUser, constant, task

SCENARIO = os.getenv("SCENARIO", "read-heavy")
READ_SHORT_CODE = os.getenv("READ_SHORT_CODE", "abc123")
LOAD_USER_ID = int(os.getenv("LOAD_USER_ID", "1"))
_COUNTER = itertools.count(int(time.time() * 1000))


def _next_suffix():
    return next(_COUNTER)


class UrlShortenerUser(FastHttpUser):
    wait_time = constant(0)

    @task
    def run_scenario(self):
        if SCENARIO == "read-heavy":
            self.read_heavy()
        elif SCENARIO == "mixed-evaluator":
            self.mixed_evaluator()
        elif SCENARIO == "write-heavy":
            self.write_heavy()
        else:
            raise RuntimeError(f"Unsupported SCENARIO={SCENARIO}")

    def read_heavy(self):
        self.client.get(
            f"/{READ_SHORT_CODE}",
            allow_redirects=False,
            name="GET /<short_code>",
        )

    def mixed_evaluator(self):
        roll = random.random()
        if roll < 0.30:
            self.client.get("/health", name="GET /health")
        elif roll < 0.50:
            self.client.get("/users", name="GET /users")
        elif roll < 0.65:
            suffix = _next_suffix()
            self.client.post(
                "/users",
                json={
                    "username": f"mixed-user-{suffix}",
                    "email": f"mixed-user-{suffix}@example.com",
                },
                name="POST /users",
            )
        elif roll < 0.80:
            suffix = _next_suffix()
            self.client.post(
                "/urls",
                json={
                    "user_id": LOAD_USER_ID,
                    "original_url": f"https://example.com/mixed/{suffix}",
                    "title": f"Mixed URL {suffix}",
                },
                name="POST /urls",
            )
        elif roll < 0.92:
            self.client.get("/urls?user_id=1", name="GET /urls")
        else:
            self.client.get("/events", name="GET /events")

    def write_heavy(self):
        roll = random.random()
        suffix = _next_suffix()
        if roll < 0.45:
            self.client.post(
                "/users",
                json={
                    "username": f"write-user-{suffix}",
                    "email": f"write-user-{suffix}@example.com",
                },
                name="POST /users",
            )
        else:
            self.client.post(
                "/urls",
                json={
                    "user_id": LOAD_USER_ID,
                    "original_url": f"https://example.com/write/{suffix}",
                    "title": f"Write URL {suffix}",
                },
                name="POST /urls",
            )
