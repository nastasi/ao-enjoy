import aiopg

# app.on_startup.append(init_pg)
async def init_pg(app):
    conf = app['config']
    print("pre")
    engine = await aiopg.create_pool(
        database=conf['pg']['name'],
        user=conf['pg']['user'],
        password=conf['pg']['passwd'],
        host=conf['pg']['host'],
        port=conf['pg']['port'],
        minsize=conf['pg']['minsize'],
        maxsize=conf['pg']['maxsize'])
    print("post")
    app['db'] = engine


async def retrieve_data(pool):
    print("p1")
    async with pool.acquire() as conn:
        print("p2")
        async with conn.cursor() as cur:
            print("p3")
            await cur.execute("SELECT 1")
            ret = []
            async for row in cur:
                ret.append(row)
                # assert ret == [(1,)]
    return ret

# app.on_cleanup.append(fini_pg)
async def fini_pg(app):
    app['db'].close()
    await app['db'].wait_closed()
