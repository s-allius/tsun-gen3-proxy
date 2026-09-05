import pytest_asyncio
import asyncio

from server import startup_app, handle_shutdown

pytest_plugins = ('pytest_asyncio',)

@pytest_asyncio.fixture(scope="session", loop_scope="session", autouse=True)
async def my_loop():
    await startup_app()

    event_loop = asyncio.get_running_loop()
    yield event_loop                     

    try:
        # We use asyncio.run, to run the async close-Methode in a clean
        # fresh and isolated Event-Loop.
        asyncio.run(handle_shutdown())
    except Exception as e:
        print(f"Error while closing the MQTT Singleton: {e}")
