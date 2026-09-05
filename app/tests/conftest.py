import pytest_asyncio
import asyncio

from server import startup_app, handle_shutdown

pytest_plugins = ('pytest_asyncio',)

@pytest_asyncio.fixture(scope="session", loop_scope="session", autouse=True)
async def my_loop():
    await startup_app()

    event_loop = asyncio.get_running_loop()
    yield event_loop                     

    await handle_shutdown()
