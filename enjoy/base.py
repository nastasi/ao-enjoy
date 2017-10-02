import os
import yaml
import asyncio
import functools
from aiohttp import web
from aiopg.sa import create_engine
from aiohttp_security import remember, forget, authorized_userid, permits
from aiohttp_session import setup as setup_session
from aiohttp_session import SimpleCookieStorage

from aiohttp_security import setup as setup_security
from aiohttp_security import SessionIdentityPolicy

from .db_auth import (check_credentials, DBAuthorizationPolicy)


def require(permission):
    def wrapper(f):
        @asyncio.coroutine
        @functools.wraps(f)
        def wrapped(self, request):
            has_perm = yield from permits(request, permission)
            if not has_perm:
                message = 'User has no permission {}'.format(permission)
                raise web.HTTPForbidden(body=message.encode())
            return (yield from f(self, request))
        return wrapped
    return wrapper


class Enjoy(object):
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
<a href="/logout">Logout</a>
</body>
</html>
"""

    @asyncio.coroutine
    def index(self, request):
        username = yield from authorized_userid(request)
        if username:
            template = self.index_template.format(
                message='Hello, {username}!'.format(username=username))
        else:
            template = self.index_template.format(message='You need to login')
        response = web.Response(body=template.encode(),
                                content_type="text/html")
        return response

    @asyncio.coroutine
    def login(self, request):
        response = web.HTTPFound('/')
        form = yield from request.post()
        login = form.get('login')
        password = form.get('password')
        db_engine = request.app.db_engine
        if (yield from check_credentials(db_engine, login, password)):
            yield from remember(request, response, login)
            return response

        return web.HTTPUnauthorized(
            body=b'Invalid username/password combination')

    @require('public')
    @asyncio.coroutine
    def logout(self, request):
        response = web.Response(body=b'You have been logged out',
                                content_type="text/html")
        yield from forget(request, response)
        return response

    @require('public')
    @asyncio.coroutine
    def internal_page(self, request):
        response = web.Response(
            body=b'This page is visible for all registered users',
            content_type="text/html")
        return response

    @require('protected')
    @asyncio.coroutine
    def protected_page(self, request):
        response = web.Response(body=b'You are on protected page',
                                content_type="text/html")
        return response

    def setup(self, app):
        with open(os.path.join('.', 'config', 'enjoy.yml')) as f:
            app['config'] = yaml.load(f)

        db_engine = yield from create_engine(user='aiohttp_security',
                                             password='aiohttp_security',
                                             database='aiohttp_security',
                                             host='127.0.0.1')
        app.db_engine = db_engine
        # setup_session(app, RedisStorage(redis_pool))
        setup_session(app, SimpleCookieStorage())
        setup_security(app,
                       SessionIdentityPolicy(),
                       DBAuthorizationPolicy(db_engine))

        app.enjoy = self
        router = app.router
        router.add_get('/', self.index)
        router.add_post('/login', self.login, name='login')
        router.add_get('/logout', self.logout, name='logout')
        router.add_get('/public', self.internal_page, name='public')
        router.add_get('/protected', self.protected_page,
                       name='protected')
