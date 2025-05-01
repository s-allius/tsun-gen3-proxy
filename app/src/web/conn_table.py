from inverter_base import InverterBase
from quart import render_template
from quart_babel import format_datetime, _
from infos import Infos

from . import web


def _get_device_icon(client_mode: bool):
    '''returns the icon for the device conntection'''
    if client_mode:
        return 'fa-download fa-rotate-180'

    return 'fa-upload fa-rotate-180'


def _get_cloud_icon(emu_mode: bool):
    '''returns the icon for the cloud conntection'''
    if emu_mode:
        return 'fa-cloud-arrow-up-alt'

    return 'fa-cloud'


def _get_row(inv: InverterBase):
    '''build one row for the connection table'''
    client_mode = inv.client_mode
    inv_serial = inv.local.stream.inv_serial
    icon1 = _get_device_icon(client_mode)
    ip1, port1 = inv.addr
    icon2 = ''
    ip2 = '--'
    port2 = '--'

    if inv.remote.ifc:
        ip2, port2 = inv.remote.ifc.r_addr
        icon2 = _get_cloud_icon(client_mode)

    row = []
    row.append(f'<i class="fa {icon1}"></i> {ip1}:{port1}')
    row.append(f'<i class="fa {icon1}"></i> {ip1}')
    row.append(inv_serial)
    row.append(f'<i class="fa {icon2}"></i> {ip2}:{port2}')
    row.append(f'<i class="fa {icon2}"></i> {ip2}')
    return row


def get_table_data():
    '''build the connection table'''
    table = {
        "col_classes": [
            "w3-hide-small w3-hide-medium", "w3-hide-large",
            "",
            "w3-hide-small w3-hide-medium", "w3-hide-large",
        ],
        "thead": [[
            _('Device-IP:Port'), _('Device-IP'),
            _("Serial-No"),
            _("Cloud-IP:Port"), _("Cloud-IP")
        ]],
        "tbody": []
    }
    for inverter in InverterBase:
        table['tbody'].append(_get_row(inverter))

    return table


@web.route('/data-fetch')
async def data_fetch():
    data = {
        "update-time": format_datetime(format="medium"),
        "server-cnt": f"<h3>{Infos.get_counter('ServerMode_Cnt')}</h3>",
        "client-cnt": f"<h3>{Infos.get_counter('ClientMode_Cnt')}</h3>",
        "proxy-cnt": f"<h3>{Infos.get_counter('ProxyMode_Cnt')}</h3>",
        "emulation-cnt": f"<h3>{Infos.get_counter('EmuMode_Cnt')}</h3>",
    }
    data["conn-table"] = await render_template('templ_conn_table.html.j2',
                                               table=get_table_data())

    data["notes-list"] = await render_template('templ_notes_list.html.j2')
    return data
