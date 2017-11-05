from unittest import TestCase
from aiohttp import web
from aiohttp.test_utils import TestClient, loop_context

from .. import Enjoy


class fake_test(TestCase):
    def test_fake_db(self):
        # loop_context is provided as a utility. You can use any
        # asyncio.BaseEventLoop class in it's place.
        with loop_context() as loop:
            enjoy = Enjoy(use_real_db=False, loop=loop)
            app = web.Application()
            app.on_startup.append(enjoy.setup)

            with TestClient(app, loop=loop) as client:

                async def test_get_route():
                    nonlocal client
                    resp = await client.get("/")
                    print(resp.status)
                    assert resp.status == 200
                    # text =
                    await resp.text()

                loop.run_until_complete(test_get_route())

    def test_real_db(self):
        # loop_context is provided as a utility. You can use any
        # asyncio.BaseEventLoop class in it's place.
        with loop_context() as loop:
            enjoy = Enjoy(use_real_db=True)
            app = web.Application()
            app.on_startup.append(enjoy.setup)

            with TestClient(app, loop=loop) as client:

                async def test_get_route():
                    nonlocal client
                    resp = await client.get("/")
                    print(resp.status)
                    assert resp.status == 200
                    # text =
                    await resp.text()

                loop.run_until_complete(test_get_route())

    def test_login(self):
        # loop_context is provided as a utility. You can use any
        # asyncio.BaseEventLoop class in it's place.
        with loop_context() as loop:
            enjoy = Enjoy(use_real_db=True)
            app = web.Application()
            app.on_startup.append(enjoy.setup)

            with TestClient(app, loop=loop) as client:

                async def test_get_route():
                    nonlocal client
                    resp = await client.post(
                        "/login", data={"login": "user",
                                        "password": "password"})
                    print(resp.status)
                    assert resp.status == 200
                    # text =
                    await resp.text()

                loop.run_until_complete(test_get_route())

    def test_logout(self):
        # loop_context is provided as a utility. You can use any
        # asyncio.BaseEventLoop class in it's place.
        with loop_context() as loop:
            enjoy = Enjoy(use_real_db=True)
            app = web.Application()
            app.on_startup.append(enjoy.setup)

            with TestClient(app, loop=loop) as client:

                async def test_get_route():
                    nonlocal client
                    resp = await client.post(
                        "/login", data={"login": "user",
                                        "password": "password"})
                    print(resp.status)
                    assert resp.status == 200
                    # text =
                    await resp.text()

                    resp = await client.get("/logout")
                    print(resp.status)
                    assert resp.status == 200
                    # text =
                    await resp.text()

                loop.run_until_complete(test_get_route())

    def test_anonymous(self):
        # loop_context is provided as a utility. You can use any
        # asyncio.BaseEventLoop class in it's place.
        with loop_context() as loop:
            enjoy = Enjoy(use_real_db=True)
            app = web.Application()
            app.on_startup.append(enjoy.setup)

            with TestClient(app, loop=loop) as client:

                async def test_get_route():
                    nonlocal client
                    resp = await client.get("/public")
                    print(resp.status)
                    assert resp.status == 403
                    # text =
                    await resp.text()

                loop.run_until_complete(test_get_route())

    def test_chat(self):
        # loop_context is provided as a utility. You can use any
        # asyncio.BaseEventLoop class in it's place.
        with loop_context() as loop:
            enjoy = Enjoy(use_real_db=True)
            app = web.Application()
            app.on_startup.append(enjoy.setup)

            with TestClient(app, loop=loop) as client:

                async def test_get_route():
                    nonlocal client
                    resp = await client.post("/login", data={
                        "login": "user",
                        "password": "password"})
                    print(resp.status)
                    assert resp.status == 200
                    # text =
                    await resp.text()

                    resp = await client.get("/chat")
                    print(resp.status)
                    assert resp.status == 200
                    # text =
                    await resp.text()

                loop.run_until_complete(test_get_route())
