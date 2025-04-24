from quart import Blueprint
from quart import render_template, url_for
from quart import send_from_directory
from quart_babel import format_datetime
from infos import Infos
from web.conn_table import get_table_data
import os

web_routes = Blueprint('web_routes', __name__)


async def get_icon(file: str, mime: str = 'image/png'):
    return await send_from_directory(
        os.path.join(web_routes.root_path, 'static/images'),
        file,
        mimetype=mime)


@web_routes.route('/')
async def index():
    return await render_template(
        'index.html.j2',
        fetch_url='.'+url_for('web_routes.data_fetch'))


@web_routes.route('/page')
async def empty():
    return await render_template('empty.html.j2')


@web_routes.route('/data-fetch')
async def data_fetch():
    data = {
        "update-time": format_datetime(format="medium"),
        "server-cnt": f"<h3>{Infos.get_counter('ServerMode_Cnt')}</h3>",
        "client-cnt": f"<h3>{Infos.get_counter('ClientMode_Cnt')}</h3>",
        "proxy-cnt": f"<h3>{Infos.get_counter('ProxyMode_Cnt')}</h3>",
        "emulation-cnt": f"<h3>{Infos.get_counter('EmuMode_Cnt')}</h3>",
    }
    data["conn-table"] = await render_template('conn_table.html.j2',
                                               table=get_table_data())

    data["notes-list"] = await render_template('notes_list.html.j2')
    return data


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
