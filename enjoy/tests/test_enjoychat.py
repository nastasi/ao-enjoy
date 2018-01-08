from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop
from aiohttp import web
from .. import EnjoyChat


class EnjoyChatFakeDBTestCase(AioHTTPTestCase):
    async def get_application(self):
        enjoy_chat = EnjoyChat(use_real_db=False)
        app = web.Application()
        app.on_startup.append(enjoy_chat.setup)

        return app

    @unittest_run_loop
    async def test_home(self):
        request = await self.client.request("GET", "/")
        assert request.status == 200
        await request.text()

    @unittest_run_loop
    async def test_login(self):
        request = await self.client.request(
            "POST", "/login", data={
                "login": "user", "password": "password"})
        assert request.status == 200
        await request.text()

    @unittest_run_loop
    async def test_wrong_login(self):
        request = await self.client.request(
            "POST", "/login", data={
                "login": "wrong_user", "password": "password"})
        assert request.status == 401
        await request.text()

    @unittest_run_loop
    async def test_public(self):
        request = await self.client.request(
            "POST", "/login", data={
                "login": "user", "password": "password"})
        assert request.status == 200
        await request.text()
        request = await self.client.request(
            "GET", "/public")
        assert request.status == 200
        await request.text()

    @unittest_run_loop
    async def test_wrong_public(self):
        request = await self.client.request(
            "GET", "/public")
        assert request.status == 403
        await request.text()

    @unittest_run_loop
    async def test_protected(self):
        request = await self.client.request(
            "POST", "/login", data={
                "login": "moderator", "password": "password"})
        assert request.status == 200
        await request.text()
        request = await self.client.request(
            "GET", "/protected")
        assert request.status == 200
        await request.text()

    @unittest_run_loop
    async def test_admin_protected(self):
        request = await self.client.request(
            "POST", "/login", data={
                "login": "admin", "password": "password"})
        assert request.status == 200
        await request.text()
        request = await self.client.request(
            "GET", "/protected")
        assert request.status == 200
        await request.text()

    @unittest_run_loop
    async def test_wrong_protected(self):
        request = await self.client.request(
            "GET", "/protected")
        assert request.status == 403
        await request.text()

    @unittest_run_loop
    async def test_wrong2_protected(self):
        request = await self.client.request(
            "POST", "/login", data={
                "login": "user", "password": "password"})
        assert request.status == 200
        await request.text()
        request = await self.client.request(
            "GET", "/protected")
        assert request.status == 403
        await request.text()

    @unittest_run_loop
    async def test_chat(self):
        request = await self.client.request(
            "POST", "/login", data={
                "login": "user", "password": "password"})
        assert request.status == 200
        await request.text()
        request = await self.client.request(
            "GET", "/chat")
        assert request.status == 200
        await request.text()

    @unittest_run_loop
    async def test_logout(self):
        request = await self.client.request(
            "POST", "/login", data={
                "login": "user", "password": "password"})
        assert request.status == 200

        request = await self.client.request(
            "GET", "/logout")
        assert request.status == 200

    @unittest_run_loop
    async def test_wrong_logout(self):
        request = await self.client.request(
            "GET", "/logout")
        assert request.status == 403
        await request.text()

    @unittest_run_loop
    async def test_wrong_sockjs_conn(self):
        request = await self.client.request(
            "POST", "/sockjs/666/sockjsss/xhr_streaming")
        assert request.status == 404
        await request.text()

    @unittest_run_loop
    async def test_sockjs_conn(self):
        request = await self.client.request(
            "POST", "/login", data={
                "login": "user", "password": "password"})
        assert request.status == 200
        await request.text()

        request = await self.client.request(
            "POST", "/sockjs/666/sockjsss/xhr_streaming")
        print(request.status)
        assert request.status == 200

    @unittest_run_loop
    async def test_sockjs_logout(self):
        request = await self.client.request(
            "POST", "/login", data={
                "login": "user", "password": "password"})
        assert request.status == 200

        request = await self.client.request(
            "POST", "/sockjs/666/sockjsss/xhr_streaming")

        request = await self.client.request(
            "GET", "/logout")
        print("REQ STAT: %d" % request.status)
        assert request.status == 200


class EnjoyChatTestCase(EnjoyChatFakeDBTestCase):
    async def get_application(self):
        enjoy = EnjoyChat(use_real_db=True)
        app = web.Application()
        app.on_startup.append(enjoy.setup)

        return app
