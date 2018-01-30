from aiohttp import web
from aiohttp.test_utils import (AioHTTPTestCase, unittest_run_loop,
                                setup_test_loop
                                )
from .. import EnjoyChat
from ..sockjs.test_utils import SockjsTest

import json


class AioHTTPMultipleClientsTestCase(AioHTTPTestCase):
    def setUp(self):
        self.loop = setup_test_loop()
        self.app = self.loop.run_until_complete(self.get_application())
        super().setUp()
        self.client2 = self.loop.run_until_complete(
            self.get_client(self.server))

    def tearDown(self):
        self.loop.run_until_complete(self.client2.close())
        super().tearDown()


class EnjoyChatFakeDBTestCase(AioHTTPMultipleClientsTestCase):
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
    async def test_sockjs_conn_wrong(self):
        sock_js = SockjsTest(self.client)
        with sock_js:
            try:
                await sock_js.connect(['xhr_streaming'], loop=self.loop)
            except AssertionError:
                self.assertEqual(sock_js.request_stream_in.status, 404)

    @unittest_run_loop
    async def test_sockjs_conn(self):
        request = await self.client.request(
            "POST", "/login", data={"login": "user", "password": "password"})
        assert request.status == 200
        await request.text()
        sock_js = SockjsTest(self.client)
        with sock_js:
            await sock_js.connect(['xhr_streaming'], loop=self.loop)
            await sock_js.send(["Test\nMessage"])
            reply_chunk = await sock_js.readchunks(1, 10, loop=self.loop)
            self.assertNotEqual(reply_chunk, None)
            self.assertEqual(json.loads(
                reply_chunk[0][0][1:].decode('utf-8')),
                ["Test\nMessage"])

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

    @unittest_run_loop
    async def test_chat_msg_login(self):
        print(self.client)
        print(self.client2)
        request = await self.client.request(
            "POST", "/login", data={
                "login": "user", "password": "password"})
        assert request.status == 200

        request2 = await self.client2.request(
            "POST", "/login", data={
                "login": "admin", "password": "password"})
        assert request2.status == 200

        sock_js = SockjsTest(self.client)
        sock_js2 = SockjsTest(self.client2)
        with sock_js2:
            await sock_js.connect(['xhr_streaming'], loop=self.loop)
            print("PRE CONNECT2: %s" % sock_js.request_stream_in.closed)
            await sock_js2.connect(['xhr_streaming'], stream=667,
                                   loop=self.loop)
            return
            print("POST CONNECT2: %s" % sock_js.request_stream_in.closed)
            await sock_js.send(["Test\nMessage"])
            reply_chunk = await sock_js.readchunks(1, 10, loop=self.loop)
            print(reply_chunk)
            self.assertNotEqual(reply_chunk, None)
            self.assertEqual(json.loads(
                reply_chunk[0][0][1:].decode('utf-8')),
                ["Test\nMessage"])

            #print(sock_js2.request_stream_in.closed)
            #reply_chunk2 = await sock_js2.readchunks(1, 10, loop=self.loop)
            #print(sock_js2.request_stream_in.closed)
            #print(reply_chunk2)
            #self.assertNotEqual(reply_chunk2, None)
            #self.assertEqual(json.loads(
            #    reply_chunk2[0][0][1:].decode('utf-8')),
            #    ["Test\nMessage"])
            
            
class EnjoyChatTestCase(EnjoyChatFakeDBTestCase):
    async def get_application(self):
        enjoy = EnjoyChat(use_real_db=True)
        app = web.Application()
        app.on_startup.append(enjoy.setup)

        return app




    # the unittest_run_loop decorator can be used in tandem with
    # the AioHTTPTestCase to simplify running
    # tests that are asynchronous
    # @unittest_run_loop
    # async def test_example(self):
    #     # pass
    #     request = await self.clients[0].request(
    #         "POST", "/login", data={"login": "user", "password": "password"})
    #     self.assertEqual(request.status, 200)

    #     request2 = await self.clients[1].request(
    #         "POST", "/login", data={"login": "admin", "password": "password"})
    #     self.assertEqual(request2.status, 200)

    #     cookie = self.clients[0].session.cookie_jar.filter_cookies(
    #         'http://127.0.0.1')

    #     aiohttp_sess = json.loads(cookie['AIOHTTP_SESSION'].value)
    #     self.assertEqual(aiohttp_sess['session']['AIOHTTP_SECURITY'], 'user')

    #     cookie = self.clients[1].session.cookie_jar.filter_cookies(
    #         'http://127.0.0.1')

    #     aiohttp_sess = json.loads(cookie['AIOHTTP_SESSION'].value)
    #     self.assertEqual(aiohttp_sess['session']['AIOHTTP_SECURITY'], 'admin')
