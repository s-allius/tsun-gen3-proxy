from quart import render_template, url_for
from quart import send_from_directory
from quart_babel import format_datetime
from infos import Infos
from web.conn_table import get_table_data
from . import web
import os


async def get_icon(file: str, mime: str = 'image/png'):
    return await send_from_directory(
        os.path.join(web.root_path, 'static/images'),
        file,
        mimetype=mime)


@web.route('/')
async def index():
    return await render_template(
        'index.html.j2',
        fetch_url='.'+url_for('web.data_fetch'))


@web.route('/page')
async def empty():
    return await render_template('empty.html.j2')


@web.route('/data-fetch')
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


@web.route('/favicon-96x96.png')
async def favicon():
    return await get_icon('favicon-96x96.png')


@web.route('/favicon.ico')
async def favicon_ico():
    return await get_icon('favicon.ico', 'image/x-icon')


@web.route('/favicon.svg')
async def favicon_svg():
    return await get_icon('favicon.svg', 'image/svg+xml')


@web.route('/apple-touch-icon.png')
async def apple_touch():
    return await get_icon('apple-touch-icon.png')


@web.route('/site.webmanifest')
async def webmanifest():
    return await get_icon('site.webmanifest', 'application/manifest+json')
