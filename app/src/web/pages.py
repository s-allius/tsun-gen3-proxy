from quart import render_template
from .wrapper import url_for

from . import web


@web.route('/')
async def index():
    return await render_template(
        'index.html.j2',
        fetch_url=url_for('web.data_fetch'))


@web.route('/page')
async def empty():
    return await render_template('empty.html.j2')
