import os
import yaml
import sockjs
import logging
import functools
import codecs
from aiohttp import web
from aiohttp_security import remember, forget, authorized_userid, permits
from aiohttp_security import setup as setup_security
from aiohttp_security import SessionIdentityPolicy

from aiohttp_session import setup as setup_session
from aiohttp_session import SimpleCookieStorage

import enjoy
from sockjs.session import (SessionManager, _marker)

from aiohttp.web import WebSocketResponse

CHAT_FILE = codecs.open(
    os.path.join(os.path.dirname(__file__), 'template',
                 'chat.html'), 'rb', encoding="utf8").read()

INDEX_FILE = codecs.open(
    os.path.join(os.path.dirname(__file__), 'template',
                 'index.html'), 'rb', encoding="utf8").read()


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


class EnjoySessionManager(SessionManager):
    async def get(self, id, create=False, request=None, default=_marker):
        print("REQUEZZ %s" % ("TRUE" if request is not False else "FALSE"))
        if request:
            print("REQUEZX %s" % request)
            username = await authorized_userid(request)
            if bool(username) is False:
                raise KeyError
        else:
            print("WOW %s" % ("True" if bool(request) else "False"))

        session = super().get(
            id, create=create, request=request)
        if session is None:
            if create:
                session = self._add(
                    self.factory(
                        id, self.handler,
                        timeout=self.timeout,
                        loop=self.loop, debug=self.debug))
            else:
                if default is not _marker:
                    return default
                raise KeyError(id)

        if request:
            enjoy = request.app.ao_enjoy
            if username in enjoy.user_sess:
                if enjoy.user_sess[username] != session:
                    print("SESSION DIFFER")
            enjoy.user_sess[username] = session
            session.ao_username = username

        session.ao_request = request
        return session


class Enjoy:
    def __init__(self, **kwargs):
        self.use_real_db = None
        if 'use_real_db' in kwargs:
            self.use_real_db = kwargs['use_real_db']

    async def index(self, request):
        username = await authorized_userid(request)
        if username:
            template = INDEX_FILE.format(
                message='Hello, {username}!'.format(username=username))
        else:
            template = INDEX_FILE.format(message='You need to login')
        response = web.Response(body=template.encode(),
                                content_type='text/html')
        return response

    async def login(self, request):
        response = web.HTTPFound('/')
        form = await request.post()
        login = form.get('login')
        password = form.get('password')
        db_engine = request.app.db_engine
        if self.use_real_db:
            from .db_auth import check_credentials
        else:
            from .db_dumb_auth import check_credentials

        if await check_credentials(db_engine, login, password):
            await remember(request, response, login)
            return response

        return web.HTTPUnauthorized(
            text='Invalid username/password combination')

    @require('public')
    async def logout(self, request):
        print("MOP LOGOUT")
        print(self.user_sess)
        username = await authorized_userid(request)
        if username:
            print("LOGOUT [%s]" % username)
            if username in self.user_sess:
                print("CLOSE QUI")

                sess = self.user_sess[username]
                if sess:
                    print(type(sess))
                    print(dir(sess))

                    manager = sess.manager
                    await sess._remote_closed()
                    if manager:
                        await manager.release(sess)
        response = web.Response(
            body='<html><body>You have been logged out<br><a href="/">'
            'Home</a></body></html>', content_type="text/html")
        await forget(request, response)
        return response

    @require('public')
    async def internal_page(self, request):
        return web.Response(
            text='This page is visible for all registered users')

    @require('protected')
    async def protected_page(self, request):
        return web.Response(text='You are on protected page')

    async def chat(self, request):
        return web.Response(body=CHAT_FILE, content_type='text/html')

    async def chat_msg_handler(self, msg, session):
        #  username = await authorized_userid(request)
        if msg.tp == sockjs.MSG_OPEN:
            session.manager.broadcast("Someone joined.")
        elif msg.tp == sockjs.MSG_MESSAGE:
            session.manager.broadcast(msg.data)
        elif msg.tp == sockjs.MSG_CLOSED:
            session.manager.broadcast("Someone left.")
            self.user_sess.pop(session.ao_username)

    async def setup(self, app):
        with open(os.path.join('.', 'config', 'enjoy.yml')) as f:
            app['config'] = yaml.load(f)

        if self.use_real_db:
            from aiopg.sa import create_engine
            db_engine = await create_engine(loop=app.loop,
                                            user='aiohttp_security',
                                            password='aiohttp_security',
                                            database='aiohttp_security',
                                            host='127.0.0.1')
        else:
            db_engine = None

        self.user_sess = dict()
        app.db_engine = db_engine
        # setup_session(app, RedisStorage(redis_pool))
        setup_session(app, SimpleCookieStorage())
        # import ipdb ; ipdb.set_trace()
        if self.use_real_db:
            from .db_auth import DBAuthorizationPolicy
            db_auth_class = DBAuthorizationPolicy
        else:
            from .db_dumb_auth import DBDumbAuthorizationPolicy
            db_auth_class = DBDumbAuthorizationPolicy

        setup_security(app,
                       SessionIdentityPolicy(),
                       db_auth_class(db_engine))

        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s %(levelname)s %(message)s')

        WebSocketResponse.prepare = require('public')(
            WebSocketResponse.prepare)

        app.ao_enjoy = self
        router = app.router
        router.add_get('/', self.index)
        router.add_static('/js/', path=os.path.join(
            os.path.dirname(__file__), 'template', 'js'), name='js')
        router.add_post('/login', self.login, name='login')
        router.add_get('/logout', self.logout, name='logout')
        router.add_get('/public', self.internal_page, name='public')
        router.add_get('/chat', self.chat, name='chat')
        router.add_get('/protected', self.protected_page,
                       name='protected')

        manager = EnjoySessionManager("chat", app, self.chat_msg_handler,
                                      app.loop)
        print(self.chat_msg_handler)

        # disable_transports = (
        #     'xhr', 'xhr_send', 'xhr_streaming',
        #     'jsonp', 'jsonp_send', 'htmlfile',
        #     'eventsource'),
        disable_transports = ()

        enjoy.add_endpoint(app, self.chat_msg_handler, name='chat',
                            manager=manager,
                            sockjs_cdn='/js/sockjs.min.js',
                            prefix='/sockjs/',
                            disable_transports=disable_transports)
