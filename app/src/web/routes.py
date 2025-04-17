from quart import Blueprint
from quart import render_template
from quart import send_from_directory
import os

web_routes = Blueprint('web_routes', __name__)


@web_routes.route('/')
async def index():
    return await render_template('index.html')


@web_routes.route('/page')
async def empty():
    return await render_template('empty.html')


@web_routes.route('/favicon.ico')
async def favicon():
    return await send_from_directory(
        os.path.join(web_routes.root_path, 'static/images'),
        'logo.png',
        mimetype='image/vnd.microsoft.icon')
