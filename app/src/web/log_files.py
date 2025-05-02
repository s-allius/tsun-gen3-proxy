from quart import render_template
from quart_babel import format_datetime, format_decimal
from quart.helpers import send_from_directory
from werkzeug.utils import secure_filename
from cnf.config import Config
import os

from . import web


def _get_file(file):
    '''build one row for the connection table'''
    entry = {}
    entry['name'] = file.name
    stat = file.stat()
    entry['size'] = format_decimal(stat.st_size)
    entry['date'] = stat.st_mtime
    entry['created'] = format_datetime(stat.st_ctime, format="short")
    entry['modified'] = format_datetime(stat.st_mtime, format="short")
    return entry


def get_list_data():
    '''build the connection table'''
    file_list = []
    with os.scandir(Config.get_log_path()) as it:
        for entry in it:
            if entry.is_file():
                file_list.append(_get_file(entry))

    file_list.sort(key=lambda x: x['date'], reverse=True)
    return file_list


@web.route('/file-fetch')
async def file_fetch():
    data = {
        "update-time": format_datetime(format="medium"),
    }
    data["file-list"] = await render_template('templ_log_files_list.html.j2',
                                              dir_list=get_list_data())

    data["notes-list"] = await render_template('templ_notes_list.html.j2')
    return data


@web.route('/send-file/<file>')
async def send(file):
    return await send_from_directory(
        directory=Config.get_log_path(),
        file_name=secure_filename(file),
        as_attachment=True)


@web.route('/del-file/<file>', methods=['DELETE'])
async def delete(file):
    try:
        os.remove(Config.get_log_path() + secure_filename(file))
    except OSError:
        return 'File not found', 404
    return '', 204
