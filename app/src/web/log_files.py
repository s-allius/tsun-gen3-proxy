from quart import render_template
from quart_babel import format_datetime, format_decimal, _
from quart.helpers import send_from_directory
from werkzeug.utils import secure_filename
from cnf.config import Config
from datetime import datetime
from os import DirEntry
import os

from . import web


def _get_birth_from_log(path: str) -> None | datetime:
    '''read timestamp from the first line of a log file'''
    dt = None
    try:
        with open(path) as f:
            first_line = f.readline()
            first_line = first_line.lstrip("'")
            fmt = "%Y-%m-%d %H:%M:%S" if first_line[4] == '-' \
                else "%d-%m-%Y %H:%M:%S"
            dt = datetime.strptime(first_line[0:19], fmt)
    except Exception:
        pass
        # print(f"except: '{e}' for {first_line}")
    return dt


def _get_file(file: DirEntry) -> dict:
    '''build one row for the connection table'''
    entry = {}
    entry['name'] = file.name
    stat = file.stat()
    entry['size'] = format_decimal(stat.st_size)
    try:
        dt = stat.st_birthtime

    except Exception:
        dt = _get_birth_from_log(file.path)

    if dt:
        entry['created'] = format_datetime(dt, format="short")

        # sort by creating date, if available
        entry['date'] = dt if isinstance(dt, float) else dt.timestamp()
    else:
        entry['created'] = _('n/a')
        entry['date'] = stat.st_mtime

    entry['modified'] = format_datetime(stat.st_mtime, format="short")
    return entry


def get_list_data() -> list:
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
