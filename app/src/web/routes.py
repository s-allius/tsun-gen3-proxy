from quart import Blueprint
from quart import Response

web_routes = Blueprint('web_routes', __name__)


@web_routes.route('/')
async def hello():
    return Response(response="Hello, world")
