from quart import Response

from server import app


@app.route('/')
async def hello():
    return Response(response="Hello, world")
