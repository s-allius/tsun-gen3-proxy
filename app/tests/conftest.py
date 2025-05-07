import pytest_asyncio
import asyncio


@pytest_asyncio.fixture
async def my_loop():
    event_loop = asyncio.get_running_loop()
    yield event_loop                     

    # Collect all tasks and cancel those that are not 'done'.  
    tasks = asyncio.all_tasks(event_loop)
    tasks = [t for t in tasks if not t.done()]
    for task in tasks:
        task.cancel()

    # Wait for all tasks to complete, ignoring any CancelledErrors                                  
    try:
        await asyncio.wait(tasks)
    except asyncio.exceptions.CancelledError:
        pass
