import os

from quart import send_from_directory

from . import web


async def get_icon(file: str, mime: str = 'image/png'):
    return await send_from_directory(
        os.path.join(web.root_path, 'static/images'),
        file,
        mimetype=mime)


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
