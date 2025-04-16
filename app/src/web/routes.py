from quart import Blueprint
from quart import render_template

web_routes = Blueprint('web_routes', __name__)


@web_routes.route('/')
async def index():
    return await render_template('index.html')


@web_routes.route('/page')
async def empty():
    return await render_template('empty.html')
