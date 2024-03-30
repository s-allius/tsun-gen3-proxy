
import struct
from typing import Generator

if __name__ == "app.src.gen3plus.infos_g3p":
    from app.src.infos import Infos, Register
else:  # pragma: no cover
    from infos import Infos, Register


class RegisterMap:
    # make the class read/only by using __slots__

    # __slots__ = ()
    map = {
        0x00d2: {'reg': Register.GRID_VOLTAGE,         'fmt': '!H', 'ratio':  0.1},  # noqa: E501
        0x00d4: {'reg': Register.GRID_CURRENT,         'fmt': '!H', 'ratio': 0.01},  # noqa: E501
        0x00d6: {'reg': Register.GRID_FREQUENCY,       'fmt': '!H', 'ratio': 0.01},  # noqa: E501
        0x00d8: {'reg': Register.INVERTER_TEMP,        'fmt': '!H', 'ratio':    1},  # noqa: E501
        0x00dc: {'reg': Register.RATED_POWER,          'fmt': '!H', 'ratio':    1},  # noqa: E501
        0x00de: {'reg': Register.OUTPUT_POWER,         'fmt': '!H', 'ratio':  0.1},  # noqa: E501
        0x00e0: {'reg': Register.PV1_VOLTAGE,          'fmt': '!H', 'ratio':  0.1},  # noqa: E501
        0x00e2: {'reg': Register.PV1_CURRENT,          'fmt': '!H', 'ratio': 0.01},  # noqa: E501
        0x00e4: {'reg': Register.PV1_POWER,            'fmt': '!H', 'ratio':  0.1},  # noqa: E501
        0x00e6: {'reg': Register.PV2_VOLTAGE,          'fmt': '!H', 'ratio':  0.1},  # noqa: E501
        0x00e8: {'reg': Register.PV2_CURRENT,          'fmt': '!H', 'ratio': 0.01},  # noqa: E501
        0x00ea: {'reg': Register.PV2_POWER,            'fmt': '!H', 'ratio':  0.1},  # noqa: E501
        0x00ec: {'reg': Register.PV3_VOLTAGE,          'fmt': '!H', 'ratio':  0.1},  # noqa: E501
        0x00ee: {'reg': Register.PV3_CURRENT,          'fmt': '!H', 'ratio': 0.01},  # noqa: E501
        0x00f0: {'reg': Register.PV3_POWER,            'fmt': '!H', 'ratio':  0.1},  # noqa: E501
        0x00f2: {'reg': Register.PV4_VOLTAGE,          'fmt': '!H', 'ratio':  0.1},  # noqa: E501
        0x00f4: {'reg': Register.PV4_CURRENT,          'fmt': '!H', 'ratio': 0.01},  # noqa: E501
        0x00f6: {'reg': Register.PV4_POWER,            'fmt': '!H', 'ratio':  0.1},  # noqa: E501
        0x00f8: {'reg': Register.DAILY_GENERATION,     'fmt': '!H', 'ratio': 0.01},  # noqa: E501
        0x00fa: {'reg': Register.TOTAL_GENERATION,     'fmt': '!L', 'ratio': 0.01},  # noqa: E501
        0x00fe: {'reg': Register.PV1_DAILY_GENERATION, 'fmt': '!H', 'ratio': 0.01},  # noqa: E501
        0x0100: {'reg': Register.PV1_TOTAL_GENERATION, 'fmt': '!L', 'ratio': 0.01},  # noqa: E501
        0x0104: {'reg': Register.PV2_DAILY_GENERATION, 'fmt': '!H', 'ratio': 0.01},  # noqa: E501
        0x0106: {'reg': Register.PV2_TOTAL_GENERATION, 'fmt': '!L', 'ratio': 0.01},  # noqa: E501
        0x010a: {'reg': Register.PV3_DAILY_GENERATION, 'fmt': '!H', 'ratio': 0.01},  # noqa: E501
        0x010c: {'reg': Register.PV3_TOTAL_GENERATION, 'fmt': '!L', 'ratio': 0.01},  # noqa: E501
        0x0110: {'reg': Register.PV4_DAILY_GENERATION, 'fmt': '!H', 'ratio': 0.01},  # noqa: E501
        0x0112: {'reg': Register.PV4_TOTAL_GENERATION, 'fmt': '!L', 'ratio': 0.01},  # noqa: E501
    }
    '''
    COMMUNICATION_TYPE = 400
    SIGNAL_STRENGTH = 401
    POWER_ON_TIME = 402
    COLLECT_INTERVAL = 403
    DATA_UP_INTERVAL = 404
    CONNECT_COUNT = 405

        COLLECTOR_FW_VERSION = 1
    CHIP_TYPE = 2
    CHIP_MODEL = 3
    TRACE_URL = 4
    LOGGER_URL = 5
    PRODUCT_NAME = 20
    MANUFACTURER = 21
    VERSION = 22
    SERIAL_NUMBER = 23
    EQUIPMENT_MODEL = 24
    NO_INPUTS = 25
    '''


class InfosG3P(Infos):
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
            res = self.ha_conf(info_id, ha_prfx, node_id, snr, False, sug_area)  # noqa: E501
            if res:
                yield res

    def parse(self, buf, ind=0) -> Generator[tuple[str, bool], None, None]:
        '''parse a data sequence received from the inverter and
        stores the values in Infos.db

        buf: buffer of the sequence to parse'''
        for addr, row in RegisterMap.map.items():
            if isinstance(row, dict):
                info_id = row['reg']
                fmt = row['fmt']
                res = struct.unpack_from(fmt, buf, addr)
                result = res[0]
                if 'ratio' in row:
                    ratio = row['ratio']
                    result *= ratio

            keys, level, unit, must_incr, new_val = self._key_obj(info_id)

            if keys:
                name, update = self.update_db(keys, must_incr, result)
                yield keys[0], update
            else:
                name = str(f'info-id.0x{addr:x}')
                update = False

            self.tracer.log(level, f'{name} : {result}{unit}'
                            f'  update: {update}')

    def ignore_this_device(self, dep: dict) -> bool:
        '''Checks the equation in the dep dict

            returns 'False' only if the equation is valid;
                    'True'  in any other case'''
        if 'reg' in dep:
            value = self.dev_value(dep['reg'])
            if not value:
                return True

            if 'gte' in dep:
                return not value >= dep['gte']
            elif 'less_eq' in dep:
                return not value <= dep['less_eq']
        return True
