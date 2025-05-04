from quart import render_template
from quart_babel import format_datetime

from . import web
from .log_handler import LogHandler


@web.route('/notes-fetch')
async def notes_fetch():
    data = {
        "update-time": format_datetime(format="medium"),
    }

    data["notes-list"] = await render_template(
        'templ_notes_list.html.j2',
        notes=LogHandler().get_buffer(),
        hide_if_empty=False)

    return data
