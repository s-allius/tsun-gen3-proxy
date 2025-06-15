from quart import render_template
from .wrapper import url_for

from . import web


@web.route('/')
async def index():
    return await render_template(
        'page_index.html.j2',
        fetch_url=url_for('.data_fetch'))


@web.route('/mqtt')
async def mqtt():
    return await render_template(
        'page_mqtt.html.j2',
        fetch_url=url_for('.mqtt_fetch'))


@web.route('/notes')
async def notes():
    return await render_template(
        'page_notes.html.j2',
        fetch_url=url_for('.notes_fetch'))


@web.route('/logging')
async def logging():
    return await render_template(
        'page_logging.html.j2',
        fetch_url=url_for('.file_fetch'))


@web.route('/network_tests')
async def network_tests():
    return await render_template(
        'page_network_tests.html.j2',
        fetch_url=url_for('.file_fetch'))
