from quart import Blueprint
from quart import render_template
from quart import send_from_directory
import os

web_routes = Blueprint('web_routes', __name__)


async def get_icon(file: str, mime: str = 'image/png'):
    return await send_from_directory(
        os.path.join(web_routes.root_path, 'static/images'),
        file,
        mimetype=mime)


@web_routes.route('/')
async def index():
    return await render_template('index.html')


@web_routes.route('/page')
async def empty():
    return await render_template('empty.html')


@web_routes.route('/favicon-96x96.png')
async def favicon():
    return await get_icon('favicon-96x96.png')


@web_routes.route('/favicon.ico')
async def favicon_ico():
    return await get_icon('favicon.ico', 'image/x-icon')


@web_routes.route('/favicon.svg')
async def favicon_svg():
    return await get_icon('favicon.svg', 'image/svg+xml')


@web_routes.route('/apple-touch-icon.png')
async def apple_touch():
    return await get_icon('apple-touch-icon.png')


@web_routes.route('/site.webmanifest')
async def webmanifest():
    return await get_icon('site.webmanifest', 'application/manifest+json')
