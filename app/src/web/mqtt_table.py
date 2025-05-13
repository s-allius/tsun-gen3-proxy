from inverter_base import InverterBase
from quart import render_template
from quart_babel import format_datetime, _
from mqtt import Mqtt

from . import web
from .log_handler import LogHandler


def _get_row(inv: InverterBase):
    '''build one row for the connection table'''
    entity_prfx = inv.entity_prfx
    inv_serial = inv.local.stream.inv_serial
    node_id = inv.local.stream.node_id
    sug_area = inv.local.stream.sug_area

    row = []
    row.append(inv_serial)
    row.append(entity_prfx+node_id)
    row.append(sug_area)
    return row


def get_table_data():
    '''build the connection table'''
    table = {
        "headline": _('MQTT devices'),
        "col_classes": [
            "",
            "",
            "",
        ],
        "thead": [[
            _("Serial-No"),
            _('Node-ID'),
            _('HA-Area'),
        ]],
        "tbody": []
    }
    for inverter in InverterBase:
        table['tbody'].append(_get_row(inverter))

    return table


@web.route('/mqtt-fetch')
async def mqtt_fetch():
    mqtt = Mqtt(None)
    cdatetime = format_datetime(dt=mqtt.ctime, format='d.MM. HH:mm')
    data = {
        "update-time": format_datetime(format="medium"),
        "mqtt-ctime": f"""
<h3 class="w3-hide-small w3-hide-medium">{cdatetime}</h3>
<h4 class="w3-hide-large">{cdatetime}</h4>
""",
        "mqtt-tx": f"<h3>{mqtt.published}</h3>",
        "mqtt-rx": f"<h3>{mqtt.received}</h3>",
    }
    data["mqtt-table"] = await render_template('templ_table.html.j2',
                                               table=get_table_data())

    data["notes-list"] = await render_template(
        'templ_notes_list.html.j2',
        notes=LogHandler().get_buffer(3),
        hide_if_empty=True)

    return data
