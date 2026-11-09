import asyncio
import os
import tempfile
import unittest

import httpx

_test_data = tempfile.TemporaryDirectory()
os.environ["DATABASE_PATH"] = os.path.join(_test_data.name, "lootdrop.db")

from app.config import settings
from app.database import create_db_and_tables, engine
from app.main import app


class TemplateRouteTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        create_db_and_tables()

    async def asyncSetUp(self):
        asyncio.get_running_loop().slow_callback_duration = 1
        self.client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://testserver",
        )

    async def asyncTearDown(self):
        await self.client.aclose()

    @classmethod
    def tearDownClass(cls):
        engine.dispose()
        _test_data.cleanup()

    async def test_public_templates_render(self):
        for path in ("/", "/subscribe", "/unsubscribe?done=1", "/admin/login"):
            with self.subTest(path=path):
                response = await self.client.get(path)
                self.assertEqual(response.status_code, 200)

    async def test_form_errors_render_templates(self):
        response = await self.client.post("/subscribe", data={"email": "invalid"})
        self.assertEqual(response.status_code, 200)

        password = "invalid-password"
        if password == settings.admin_password:
            password += "-wrong"
        response = await self.client.post(
            "/admin/login",
            data={"username": settings.admin_username, "password": password},
        )
        self.assertEqual(response.status_code, 200)

    async def test_authenticated_admin_templates_render(self):
        response = await self.client.post(
            "/admin/login",
            data={
                "username": settings.admin_username,
                "password": settings.admin_password,
            },
        )
        self.assertEqual(response.status_code, 303)

        for path in ("/admin/dashboard", "/admin/giveaways", "/admin/subscribers"):
            with self.subTest(path=path):
                response = await self.client.get(path)
                self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
