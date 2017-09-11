from aiohttp import web
from enjoy.db_api import retrieve_data

async def index(request):
    print("index: begin")
    ret = await retrieve_data(request.app['db'])
    return web.Response(text='Hello ' + str(ret[0][0]) + ' Aiohttp!')
