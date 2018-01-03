import asyncio
import random
import logging
import inspect
from aiohttp import web, hdrs

from sockjs.session import SessionManager
from sockjs.route import SockJSRoute

from sockjs.transports import handlers
from sockjs.transports.utils import session_cookie
from sockjs.transports.rawwebsocket import RawWebSocketTransport

log = logging.getLogger('sockjs')


def _gen_endpoint_name():
    return 'n' + str(random.randint(1000, 9999))


def add_endpoint(app, handler, *, name='', prefix='/sockjs',
                 manager=None, disable_transports=(),
                 sockjs_cdn='http://cdn.sockjs.org/sockjs-0.3.3.min.js',
                 cookie_needed=True):

    assert callable(handler), handler
    if (not asyncio.iscoroutinefunction(handler) and
            not inspect.isgeneratorfunction(handler)):
        handler = asyncio.coroutine(handler)

    router = app.router

    if not name:
        name = _gen_endpoint_name()

    # set session manager
    if manager is None:
        manager = SessionManager(name, app, handler, app.loop)

    if manager.name != name:
        raise ValueError(
            'Session manage must have same name as sockjs route')

    managers = app.setdefault('__sockjs_managers__', {})
    if name in managers:
        raise ValueError('SockJS "%s" route already registered' % name)

    managers[name] = manager

    # register routes
    route = EnjoySockJSRoute(
        name, manager, sockjs_cdn,
        handlers, disable_transports, cookie_needed)

    if prefix.endswith('/'):
        prefix = prefix[:-1]

    route_name = 'sockjs-url-%s-greeting' % name
    router.add_route(
        hdrs.METH_GET, prefix, route.greeting, name=route_name)

    route_name = 'sockjs-url-%s' % name
    router.add_route(
        hdrs.METH_GET, '%s/' % prefix,
        route.greeting, name=route_name)

    route_name = 'sockjs-%s' % name
    router.add_route(
        hdrs.METH_ANY,
        '%s/{server}/{session}/{transport}' % prefix,
        route.handler, name=route_name)

    route_name = 'sockjs-websocket-%s' % name
    router.add_route(
        hdrs.METH_GET, '%s/websocket' % prefix,
        route.websocket, name=route_name)

    router.add_route(
        hdrs.METH_GET, '%s/info' % prefix,
        route.info, name='sockjs-info-%s' % name)
    router.add_route(
        hdrs.METH_OPTIONS,
        '%s/info' % prefix,
        route.info_options, name='sockjs-info-options-%s' % name)

    route_name = 'sockjs-iframe-%s' % name
    router.add_route(
        hdrs.METH_GET,
        '%s/iframe.html' % prefix, route.iframe, name=route_name)

    route_name = 'sockjs-iframe-ver-%s' % name
    router.add_route(
        hdrs.METH_GET,
        '%s/iframe{version}.html' % prefix, route.iframe, name=route_name)

    # start session gc
    manager.start()


class EnjoySockJSRoute(SockJSRoute):

    @asyncio.coroutine
    def handler(self, request):
        info = request.match_info

        # lookup transport
        tid = info['transport']

        if tid not in self.handlers or tid in self.disable_transports:
            return web.HTTPNotFound()

        create, transport = self.handlers[tid]

        # session
        manager = self.manager
        if not manager.started:
            manager.start()

        sid = info['session']
        if not sid or '.' in sid or '.' in info['server']:
            return web.HTTPNotFound()

        try:
            session = yield from manager.get(sid, create, request=request)
        except KeyError:
            return web.HTTPNotFound(headers=session_cookie(request))

        t = transport(manager, session, request)
        try:
            return (yield from t.process())
        except asyncio.CancelledError:
            raise
        except web.HTTPException as exc:
            return exc
        except Exception as exc:
            log.exception('Exception in transport: %s' % tid)
            if manager.is_acquired(session):
                yield from manager.release(session)
            return web.HTTPInternalServerError()

    @asyncio.coroutine
    def websocket(self, request):
        # session
        sid = '%0.9d' % random.randint(1, 2147483647)
        session = yield from self.manager.get(sid, True, request=request)

        transport = RawWebSocketTransport(self.manager, session, request)
        try:
            return (yield from transport.process())
        except asyncio.CancelledError:
            raise
        except web.HTTPException as exc:
            return exc
