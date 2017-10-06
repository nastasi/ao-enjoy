import asyncio

from aiohttp_security.abc import AbstractAuthorizationPolicy

# singleton with data
_base = None


class DBDumbAuthorizationPolicy(AbstractAuthorizationPolicy):
    def __init__(self, db_engine):
        global _base

        if _base is None:
            _base = self
        self.users = {
            'admin': {
                'id': 1,
                'password': 'password',
                'is_superuser': True,
                'disabled': False},
            'moderator': {
                'id': 2,
                'password': 'password',
                'is_superuser': False,
                'disabled': False},
            'user': {
                'id': 3,
                'password': 'password',
                'is_superuser': False,
                'disabled': False},
            'disabled': {
                'id': 4,
                'password': 'password',
                'is_superuser': False,
                'disabled': True},
            }
        self.perms = {
            ('moderator', 'protected'): True,
            ('moderator', 'public'): True,
            ('user', 'public'): True,
            }

    @asyncio.coroutine
    def authorized_userid(self, identity):
        if (identity in self.users and
                self.users[identity]['disabled'] is False):
            return identity
        else:
            return None

    @asyncio.coroutine
    def permits(self, identity, permission, context=None):
        if identity is None:
            return False

        if identity not in self.users:
            return False

        user = self.users[identity]

        if user['disabled'] is True:
            return False

        if user['is_superuser'] is True:
            return True

        if (identity, permission) in self.perms:
            return True

        return False


@asyncio.coroutine
def check_credentials(db_engine, username, password):
    print("CC")
    if username in _base.users:
        print("CC2")
        if _base.users[username]['password'] == password:
            print("CC3")
            return True

    return False
