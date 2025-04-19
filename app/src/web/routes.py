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


def get_inv_count():
    return 1234


TsunCnt = 0


def get_tsun_count():
    global TsunCnt
    TsunCnt += 1
    return TsunCnt


@web_routes.context_processor
def utility_processor():
    return dict(inv_count=get_inv_count(),
                tsun_count=get_tsun_count())


@web_routes.route('/')
async def index():
    return await render_template('index.html.j2', fetch_url='/data-fetch')


@web_routes.route('/page')
async def empty():
    return await render_template('empty.html.j2')


@web_routes.route('/data-fetch')
async def data_fetch():
    global TsunCnt
    TsunCnt += 1
    return {
        "geology-fact": f"<h3>{TsunCnt}</h3>",
    }


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
