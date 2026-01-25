# tests/test_routes.py

# -*- coding: utf-8 -*-
# Copyright ...

import os
import unittest
import ujson as json
from httpx import AsyncClient, ASGITransport
from starlette.types import ASGIApp
from fq_server import setup_server
from fq_server.server import FQServer


class FQConfigTestCase(unittest.TestCase):
    """Tests for configuration validation."""

    def test_missing_fq_config_env_var(self):
        """Test that missing FQ_CONFIG environment variable raises an error."""
        # Ensure FQ_CONFIG is not set
        env_backup = os.environ.pop("FQ_CONFIG", None)
        try:
            with self.assertRaises(EnvironmentError) as context:
                # Re-import asgi module to trigger the check
                import importlib
                import asgi

                importlib.reload(asgi)
            self.assertIn("FQ_CONFIG", str(context.exception))
        finally:
            # Restore the environment variable if it was set
            if env_backup is not None:
                os.environ["FQ_CONFIG"] = env_backup

    def test_config_file_not_found(self):
        """Test that non-existent config file raises FileNotFoundError."""
        with self.assertRaises(FileNotFoundError) as context:
            FQServer("/nonexistent/path/to/config.conf")
        self.assertIn("Config file not found", str(context.exception))


class FQServerTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # build server and Starlette app
        config_path = os.path.join(os.path.dirname(__file__), "test.conf")
        server = setup_server(config_path)
        self.server = server
        self.app: ASGIApp = server.app

        # queue + redis client (async)
        self.queue = server.queue
        await self.queue._initialize()  # important: same loop as tests
        self.r = self.queue._r

        # flush redis before each test
        await self.r.flushdb()

        # async HTTP client bound to this ASGI app & this loop
        transport = ASGITransport(app=self.app)
        self.client = AsyncClient(transport=transport, base_url="http://test")

    async def asyncTearDown(self):
        # flush redis after each test
        await self.r.flushdb()
        await self.client.aclose()

    async def test_root(self):
        response = await self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Hello, FQS!"})

    async def test_enqueue(self):
        request_params = {
            "job_id": "ef022088-d2b3-44ad-bf0d-a93d6d93b82c",
            "payload": {"message": "Hello, world."},
            "interval": 1000,
        }
        response = await self.client.post(
            "/enqueue/sms/johdoe/",
            content=json.dumps(request_params),
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["status"], "queued")

        request_params = {
            "job_id": "ef022088-d2b3-44ad-bf1d-a93d6d93b82c",
            "payload": {"message": "Hello, world."},
            "interval": 1000,
            "requeue_limit": 10,
        }
        response = await self.client.post(
            "/enqueue/sms/johdoe/",
            content=json.dumps(request_params),
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["status"], "queued")

    async def test_dequeue_fail(self):
        response = await self.client.get("/dequeue/")
        # your Starlette handler returns 400 or 404 – pick what your code actually does
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["status"], "failure")

        response = await self.client.get("/dequeue/sms/")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["status"], "failure")

    async def test_dequeue(self):
        # enqueue a job
        request_params = {
            "job_id": "ef022088-d2b3-44ad-bf0d-a93d6d93b82c",
            "payload": {"message": "Hello, world."},
            "interval": 1000,
        }
        await self.client.post(
            "/enqueue/sms/johndoe/",
            content=json.dumps(request_params),
            headers={"Content-Type": "application/json"},
        )

        # dequeue a job
        response = await self.client.get("/dequeue/sms/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["job_id"], "ef022088-d2b3-44ad-bf0d-a93d6d93b82c")
        self.assertEqual(data["payload"], {"message": "Hello, world."})
        self.assertEqual(data["queue_id"], "johndoe")
        self.assertEqual(data["requeues_remaining"], -1)  # from config

    async def test_finish_fail(self):
        response = await self.client.post(
            "/finish/sms/johndoe/ef022088-d2b3-44ad-bf0d-a93d6d93b82c/"
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["status"], "failure")

    async def test_finish(self):
        # enqueue a job
        request_params = {
            "job_id": "ef022088-d2b3-44ad-bf0d-a93d6d93b82c",
            "payload": {"message": "Hello, world."},
            "interval": 1000,
        }
        await self.client.post(
            "/enqueue/sms/johndoe/",
            content=json.dumps(request_params),
            headers={"Content-Type": "application/json"},
        )

        # dequeue a job
        await self.client.get("/dequeue/sms/")

        # mark it as finished
        response = await self.client.post(
            "/finish/sms/johndoe/ef022088-d2b3-44ad-bf0d-a93d6d93b82c/"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")

    async def test_interval(self):
        # enqueue a job
        request_params = {
            "job_id": "ef022088-d2b3-44ad-bf0d-a93d6d93b82c",
            "payload": {"message": "Hello, world."},
            "interval": 1000,
        }
        await self.client.post(
            "/enqueue/sms/johndoe/",
            content=json.dumps(request_params),
            headers={"Content-Type": "application/json"},
        )

        # change the interval
        request_params = {"interval": 5000}
        response = await self.client.post(
            "/interval/sms/johndoe/",
            content=json.dumps(request_params),
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.json()["status"], "success")

    async def test_interval_fail(self):
        request_params = {"interval": 5000}
        response = await self.client.post(
            "/interval/sms/johndoe/",
            content=json.dumps(request_params),
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.json()["status"], "failure")

    async def test_metrics(self):
        response = await self.client.get("/metrics/")
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("queue_types", data)
        self.assertIn("enqueue_counts", data)
        self.assertIn("dequeue_counts", data)

    async def test_metrics_with_queue_type(self):
        response = await self.client.get("/metrics/sms/")
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("queue_ids", data)

    async def test_metrics_with_queue_type_and_queue_id(self):
        response = await self.client.get("/metrics/sms/johndoe/")
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("queue_length", data)
        self.assertIn("enqueue_counts", data)
        self.assertIn("dequeue_counts", data)


if __name__ == "__main__":
    unittest.main()
