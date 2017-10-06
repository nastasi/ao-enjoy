import os
import yaml
import sockjs
import asyncio
import logging
import functools
from aiohttp import web
from aiohttp_security import remember, forget, authorized_userid, permits
from aiohttp_session import setup as setup_session
from aiohttp_session import SimpleCookieStorage

from aiohttp_security import setup as setup_security
from aiohttp_security import SessionIdentityPolicy

from aiohttp.web import WebSocketResponse

USE_REAL_DB = False
if USE_REAL_DB is True:
    from aiopg.sa import create_engine
    from .db_auth import (check_credentials, DBAuthorizationPolicy)
else:
    from .db_dumb_auth import (check_credentials, DBDumbAuthorizationPolicy)

CHAT_FILE = open(
    os.path.join(os.path.dirname(__file__), 'template',
                 'chat.html'), 'rb').read()


def require(permission):
    def wrapper(f):

        @functools.wraps(f)
        async def wrapped(self, request):
            has_perm = await permits(request, permission)
            if not has_perm:
                message = 'User has no permission {}'.format(permission)
                raise web.HTTPForbidden(text=message)
            return await f(self, request)
        return wrapped
    return wrapper


class Enjoy:

    index_template = """<!doctype html>
<head>
</head>
<body>
<p>{message}</p>
<form action="/login" method="post">
  Login:
  <input type="text" name="login">
  Password:
  <input type="password" name="password">
  <input type="submit" value="Login">
</form>
<a href="/logout">Logout</a>
</body>
"""

    index_template = """
<!doctype html>
<html>
<head>
</head>
<body>
<p>{message}</p>
<form action="/login" method="post">
  Login:
  <input type="text" name="login">
  Password:
  <input type="password" name="password">
  <input type="submit" value="Login">
</form>
<a href="/public">Public</a><br>
<a href="/protected">Protected</a><br>
<a href="/chat">Chat</a><br>
<a href="/logout">Logout</a>
</body>
</html>
"""

    async def index(self, request):
        username = await authorized_userid(request)
        if username:
            template = self.index_template.format(
                message='Hello, {username}!'.format(username=username))
        else:
            template = self.index_template.format(message='You need to login')
        response = web.Response(body=template.encode(),
                                content_type='text/html')
        return response

    async def login(self, request):
        response = web.HTTPFound('/')
        form = await request.post()
        login = form.get('login')
        password = form.get('password')
        db_engine = request.app.db_engine
        if await check_credentials(db_engine, login, password):
            await remember(request, response, login)
            return response

        return web.HTTPUnauthorized(
            text='Invalid username/password combination')

    @require('public')
    async def logout(self, request):
        response = web.Response(body=b'You have been logged out',
                                content_type="text/html")
        await forget(request, response)
        return response

    @require('public')
    async def internal_page(self, request):
        return web.Response(
            text='This page is visible for all registered users')

    @require('protected')
    async def protected_page(self, request):
        return web.Response(text='You are on protected page')

#    @require('public')
    async def chat(self, request):
        return web.Response(body=CHAT_FILE, content_type='text/html')

    def chat_msg_handler(self, msg, session):
        if msg.tp == sockjs.MSG_OPEN:
            session.manager.broadcast("Someone joined.")
        elif msg.tp == sockjs.MSG_MESSAGE:
            session.manager.broadcast(msg.data)
        elif msg.tp == sockjs.MSG_CLOSED:
            session.manager.broadcast("Someone left.")

    async def setup(self, app):
        with open(os.path.join('.', 'config', 'enjoy.yml')) as f:
            app['config'] = yaml.load(f)

        if USE_REAL_DB is True:
            db_engine = await create_engine(user='aiohttp_security',
                                            password='aiohttp_security',
                                            database='aiohttp_security',
                                            host='127.0.0.1')
        else:
            db_engine = None

        app.db_engine = db_engine
        # setup_session(app, RedisStorage(redis_pool))
        setup_session(app, SimpleCookieStorage())
        # import ipdb ; ipdb.set_trace()
        if USE_REAL_DB is True:
            db_auth_class = DBAuthorizationPolicy
        else:
            db_auth_class = DBDumbAuthorizationPolicy

        setup_security(app,
                       SessionIdentityPolicy(),
                       db_auth_class(db_engine))

        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s %(levelname)s %(message)s')

        WebSocketResponse.prepare = require('public')(WebSocketResponse.prepare)

        app.enjoy = self
        router = app.router
        router.add_get('/', self.index)
        router.add_post('/login', self.login, name='login')
        router.add_get('/logout', self.logout, name='logout')
        router.add_get('/public', self.internal_page, name='public')
        router.add_get('/chat', self.chat, name='chat')
        router.add_get('/protected', self.protected_page,
                       name='protected')

        sockjs.add_endpoint(app, self.chat_msg_handler, name='chat',
                            prefix='/sockjs/')
