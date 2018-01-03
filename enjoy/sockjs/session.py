import asyncio
import logging

try:
    from asyncio import ensure_future
except ImportError:  # pragma: no cover
    ensure_future = asyncio.async

from sockjs.session import SessionManager


log = logging.getLogger('sockjs')


_marker = object()


class EnjoySessionManagerBase(SessionManager):
    """A basic session manager with async get method."""

    @asyncio.coroutine
    def get(self, id, create=False, request=None, default=_marker):
        session = super(SessionManager, self).get(id, None)
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

        return session
