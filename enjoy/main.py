#!/usr/bin/env python
import os
import yaml
from aiohttp import web
from routes import setup_routes
from enjoy.db_api import (init_pg, fini_pg)

app = web.Application()
app.on_startup.append(init_pg)
app.on_cleanup.append(fini_pg)

with open(os.path.join('.', 'config', 'enjoy.yml')) as f:
    app['config'] = yaml.load(f)

setup_routes(app)
web.run_app(app, host='127.0.0.1', port=8080)
