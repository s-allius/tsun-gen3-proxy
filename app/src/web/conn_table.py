from inverter_base import InverterBase


def _get_row2():
    icon1 = 'fa-upload fa-rotate-180'
    ip1 = '192.168.200.194'
    port1 = '39000'
    icon2 = 'fa-cloud'
    ip2 = '188.168.200.194'
    port2 = '10000'
    row = []
    row.append(f'<i class="fa {icon1}"></i> {ip1}:{port1}')
    row.append(f'<i class="fa {icon1}"></i> {ip1}')
    row.append("Y170000000000001")
    row.append(f'<i class="fa {icon2}"></i> {ip2}:{port2}')
    row.append(f'<i class="fa {icon2}"></i> {ip2}')
    return row


def _get_device_icon(client_mode: bool):
    if client_mode:
        return 'fa-download fa-rotate-180'

    return 'fa-upload fa-rotate-180'


def _get_cloud_icon(emu_mode: bool):
    if emu_mode:
        return 'fa-cloud-arrow-down-alt'

    return 'fa-cloud'


def _get_row(inv: InverterBase):
    ip1, port1 = inv.addr
    client_mode = inv.client_mode
    icon1 = ''
    icon2 = ''
    ip2 = '--'
    port2 = '--'
    inv_serial = ''
    if inv.local.stream:
        inv_serial = inv.local.stream.inv_serial
        icon1 = _get_device_icon(client_mode)

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
    table = {
        "col_classes": [
            "w3-hide-small w3-hide-medium", "w3-hide-large",
            "",
            "w3-hide-small w3-hide-medium", "w3-hide-large",
        ],
        "thead": [[
            'Device-IP:Port', 'Device-IP',
            "Serial-No",
            "Cloud-IP:Port", "Cloud-IP"
        ]],
        "tbody": []
    }
    table['tbody'].append(_get_row2())
    for inverter in InverterBase:
        table['tbody'].append(_get_row(inverter))

    return table
