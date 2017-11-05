#!/usr/bin/env python
from aiohttp import web
from enjoy import Enjoy


def main():
    enjoy = Enjoy(use_real_db=False)

    app = web.Application()
    app.on_startup.append(enjoy.setup)

    web.run_app(app, host='127.0.0.1', port=8080)


if __name__ == '__main__':
    main()
