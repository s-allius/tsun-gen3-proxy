
import struct
from typing import Generator

if __name__ == "app.src.gen3plus.infos_g3p":
    from app.src.infos import Infos, Register, ProxyMode
else:  # pragma: no cover
    from infos import Infos, Register, ProxyMode


class RegisterMap:
    # make the class read/only by using __slots__

    __slots__ = ()
    map = {
        # 0x41020007: {'reg': Register.DEVICE_SNR,           'fmt': '<L'},                 # noqa: E501
        0x41020018: {'reg': Register.DATA_UP_INTERVAL,     'fmt': '<B', 'ratio':   60, 'dep': ProxyMode.SERVER},  # noqa: E501
        0x41020019: {'reg': Register.COLLECT_INTERVAL,     'fmt': '<B', 'eval': 'round(result/60)', 'dep': ProxyMode.SERVER},  # noqa: E501
        0x4102001a: {'reg': Register.HEARTBEAT_INTERVAL,   'fmt': '<B', 'ratio':    1},  # noqa: E501
        0x4102001c: {'reg': Register.SIGNAL_STRENGTH,      'fmt': '<B', 'ratio':    1, 'dep': ProxyMode.SERVER},  # noqa: E501
        0x4102001e: {'reg': Register.CHIP_MODEL,           'fmt': '!40s'},               # noqa: E501
        0x4102004c: {'reg': Register.IP_ADDRESS,           'fmt': '!16s'},               # noqa: E501
        0x41020064: {'reg': Register.COLLECTOR_FW_VERSION, 'fmt': '!40s'},               # noqa: E501

        0x4201001c: {'reg': Register.POWER_ON_TIME,        'fmt': '<H', 'ratio':    1, 'dep': ProxyMode.SERVER},  # noqa: E501
        0x42010020: {'reg': Register.SERIAL_NUMBER,        'fmt': '!16s'},               # noqa: E501
        0x420100c0: {'reg': Register.INVERTER_STATUS,      'fmt': '!H'},                 # noqa: E501
        0x420100d0: {'reg': Register.VERSION,              'fmt': '!H', 'eval': "f'V{(result>>12)}.{(result>>8)&0xf}.{(result>>4)&0xf}{result&0xf}'"},  # noqa: E501
        0x420100d2: {'reg': Register.GRID_VOLTAGE,         'fmt': '!H', 'ratio':  0.1},  # noqa: E501
        0x420100d4: {'reg': Register.GRID_CURRENT,         'fmt': '!H', 'ratio': 0.01},  # noqa: E501
        0x420100d6: {'reg': Register.GRID_FREQUENCY,       'fmt': '!H', 'ratio': 0.01},  # noqa: E501
        0x420100d8: {'reg': Register.INVERTER_TEMP,        'fmt': '!H', 'eval': 'result-40'},  # noqa: E501
        # 0x420100d8: {'reg': Register.INVERTER_TEMP,        'fmt': '!H'},                 # noqa: E501
        0x420100dc: {'reg': Register.RATED_POWER,          'fmt': '!H', 'ratio':    1},  # noqa: E501
        0x420100de: {'reg': Register.OUTPUT_POWER,         'fmt': '!H', 'ratio':  0.1},  # noqa: E501
        0x420100e0: {'reg': Register.PV1_VOLTAGE,          'fmt': '!H', 'ratio':  0.1},  # noqa: E501
        0x420100e2: {'reg': Register.PV1_CURRENT,          'fmt': '!H', 'ratio': 0.01},  # noqa: E501
        0x420100e4: {'reg': Register.PV1_POWER,            'fmt': '!H', 'ratio':  0.1},  # noqa: E501
        0x420100e6: {'reg': Register.PV2_VOLTAGE,          'fmt': '!H', 'ratio':  0.1},  # noqa: E501
        0x420100e8: {'reg': Register.PV2_CURRENT,          'fmt': '!H', 'ratio': 0.01},  # noqa: E501
        0x420100ea: {'reg': Register.PV2_POWER,            'fmt': '!H', 'ratio':  0.1},  # noqa: E501
        0x420100ec: {'reg': Register.PV3_VOLTAGE,          'fmt': '!H', 'ratio':  0.1},  # noqa: E501
        0x420100ee: {'reg': Register.PV3_CURRENT,          'fmt': '!H', 'ratio': 0.01},  # noqa: E501
        0x420100f0: {'reg': Register.PV3_POWER,            'fmt': '!H', 'ratio':  0.1},  # noqa: E501
        0x420100f2: {'reg': Register.PV4_VOLTAGE,          'fmt': '!H', 'ratio':  0.1},  # noqa: E501
        0x420100f4: {'reg': Register.PV4_CURRENT,          'fmt': '!H', 'ratio': 0.01},  # noqa: E501
        0x420100f6: {'reg': Register.PV4_POWER,            'fmt': '!H', 'ratio':  0.1},  # noqa: E501
        0x420100f8: {'reg': Register.DAILY_GENERATION,     'fmt': '!H', 'ratio': 0.01},  # noqa: E501
        0x420100fa: {'reg': Register.TOTAL_GENERATION,     'fmt': '!L', 'ratio': 0.01},  # noqa: E501
        0x420100fe: {'reg': Register.PV1_DAILY_GENERATION, 'fmt': '!H', 'ratio': 0.01},  # noqa: E501
        0x42010100: {'reg': Register.PV1_TOTAL_GENERATION, 'fmt': '!L', 'ratio': 0.01},  # noqa: E501
        0x42010104: {'reg': Register.PV2_DAILY_GENERATION, 'fmt': '!H', 'ratio': 0.01},  # noqa: E501
        0x42010106: {'reg': Register.PV2_TOTAL_GENERATION, 'fmt': '!L', 'ratio': 0.01},  # noqa: E501
        0x4201010a: {'reg': Register.PV3_DAILY_GENERATION, 'fmt': '!H', 'ratio': 0.01},  # noqa: E501
        0x4201010c: {'reg': Register.PV3_TOTAL_GENERATION, 'fmt': '!L', 'ratio': 0.01},  # noqa: E501
        0x42010110: {'reg': Register.PV4_DAILY_GENERATION, 'fmt': '!H', 'ratio': 0.01},  # noqa: E501
        0x42010112: {'reg': Register.PV4_TOTAL_GENERATION, 'fmt': '!L', 'ratio': 0.01},  # noqa: E501
        0x42010126: {'reg': Register.MAX_DESIGNED_POWER,   'fmt': '!H', 'ratio':    1},  # noqa: E501

        0xffffff01: {'reg': Register.OUTPUT_COEFFICIENT},
        0xffffff02: {'reg': Register.POLLING_INTERVAL},
        # 0x4281001c: {'reg': Register.POWER_ON_TIME,        'fmt': '<H', 'ratio':    1},  # noqa: E501

    }


class InfosG3P(Infos):
    def __init__(self, client_mode: bool):
        super().__init__()
        self.client_mode = client_mode
        self.set_db_def_value(Register.MANUFACTURER, 'TSUN')
        self.set_db_def_value(Register.EQUIPMENT_MODEL, 'TSOL-MSxx00')
        self.set_db_def_value(Register.CHIP_TYPE, 'IGEN TECH')
        self.set_db_def_value(Register.NO_INPUTS, 4)

    def __hide_topic(self, row: dict) -> bool:
        if 'dep' in row:
            mode = row['dep']
            if self.client_mode:
                return mode != ProxyMode.CLIENT
            else:
                return mode != ProxyMode.SERVER
        return False

    def ha_confs(self, ha_prfx: str, node_id: str, snr: str,
                 sug_area: str = '') \
            -> Generator[tuple[dict, str], None, None]:
        '''Generator function yields a json register struct for home-assistant
        auto configuration and a unique entity string

        arguments:
        prfx:str     ==> MQTT prefix for the home assistant 'stat_t string
        snr:str      ==> serial number of the inverter, used to build unique
                         entity strings
        sug_area:str ==> suggested area string from the config file'''
        # iterate over RegisterMap.map and get the register values
        for row in RegisterMap.map.values():
            info_id = row['reg']
            if self.__hide_topic(row):
                res = self.ha_remove(info_id, node_id, snr)  # noqa: E501
            else:
                res = self.ha_conf(info_id, ha_prfx, node_id, snr, False, sug_area)  # noqa: E501
            if res:
                yield res

    def parse(self, buf, msg_type: int, rcv_ftype: int, node_id: str = '') \
            -> Generator[tuple[str, bool], None, None]:
        '''parse a data sequence received from the inverter and
        stores the values in Infos.db

        buf: buffer of the sequence to parse'''
        for idx, row in RegisterMap.map.items():
            addr = idx & 0xffff
            ftype = (idx >> 16) & 0xff
            mtype = (idx >> 24) & 0xff
            if ftype != rcv_ftype or mtype != msg_type:
                continue
            if not isinstance(row, dict):
                continue
            info_id = row['reg']
            result = self.__get_value(buf, addr, row)

            keys, level, unit, must_incr = self._key_obj(info_id)

            if keys:
                name, update = self.update_db(keys, must_incr, result)
                yield keys[0], update
            else:
                name = str(f'info-id.0x{addr:x}')
                update = False

            if update:
                self.tracer.log(level, f'[{node_id}] GEN3PLUS: {name}'
                                       f' : {result}{unit}')

    def __get_value(self, buf, idx, row):
        '''Get a value from buf and interpret as in row'''
        fmt = row['fmt']
        res = struct.unpack_from(fmt, buf, idx)
        result = res[0]
        if isinstance(result, (bytearray, bytes)):
            result = result.decode().split('\x00')[0]
        if 'eval' in row:
            result = eval(row['eval'])
        if 'ratio' in row:
            result = round(result * row['ratio'], 2)
        return result
