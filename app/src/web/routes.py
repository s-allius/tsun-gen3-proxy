from quart import Blueprint
from quart import render_template

web_routes = Blueprint('web_routes', __name__)


@web_routes.route('/')
async def hello():
    return await render_template('index.html')
