
import struct
import logging
from typing import Generator
from itertools import chain

from infos import Infos, Register


class RegisterMap:
    __slots__ = ()
    map = {
        0xffffff00: {'reg': Register.INVERTER_CNT},
        0xffffff01: {'reg': Register.UNKNOWN_SNR},
        0xffffff02: {'reg': Register.UNKNOWN_MSG},
        0xffffff03: {'reg': Register.INVALID_DATA_TYPE},
        0xffffff04: {'reg': Register.INTERNAL_ERROR},
        0xffffff05: {'reg': Register.UNKNOWN_CTRL},
        0xffffff06: {'reg': Register.OTA_START_MSG},
        0xffffff07: {'reg': Register.SW_EXCEPTION},
        0xffffff08: {'reg': Register.POLLING_INTERVAL},
        0xfffffffe: {'reg': Register.TEST_REG1},
        0xffffffff: {'reg': Register.TEST_REG2},
    }
    map_0e100000 = {
        0x00092ba8: {'reg': Register.COLLECTOR_FW_VERSION},
        0x000927c0: {'reg': Register.CHIP_TYPE},
        0x00092f90: {'reg': Register.CHIP_MODEL},
        0x00094ae8: {'reg': Register.MAC_ADDR},
        0x00095a88: {'reg': Register.TRACE_URL},
        0x00095aec: {'reg': Register.LOGGER_URL},
        0x000cfc38: {'reg': Register.CONNECT_COUNT},
        0x000c3500: {'reg': Register.SIGNAL_STRENGTH},
        0x000c96a8: {'reg': Register.POWER_ON_TIME},
        0x000d0020: {'reg': Register.COLLECT_INTERVAL},
        0x000cf850: {'reg': Register.DATA_UP_INTERVAL},
        0x000c7f38: {'reg': Register.COMMUNICATION_TYPE},
    }
    map_01900000 = {
        0x00000064: {'reg': Register.INVERTER_STATUS},
        0x00000190: {'reg': Register.EVENT_ALARM},
        0x000001f4: {'reg': Register.EVENT_FAULT},
        0x00000258: {'reg': Register.EVENT_BF1},
        0x000002bc: {'reg': Register.EVENT_BF2},
        0x00000640: {'reg': Register.GRID_FREQUENCY},
        0x00000834: {'reg': Register.MAX_DESIGNED_POWER},
    }
    map_01900001 = {
        0x0000000a: {'reg': Register.PRODUCT_NAME},
        0x00000014: {'reg': Register.MANUFACTURER},
        0x0000001e: {'reg': Register.VERSION},
        0x00000028: {'reg': Register.SERIAL_NUMBER},
        0x00000032: {'reg': Register.EQUIPMENT_MODEL},
        0x00013880: {'reg': Register.NO_INPUTS},
        0x00000640: {'reg': Register.OUTPUT_POWER},
        0x000005dc: {'reg': Register.RATED_POWER},
        0x00000514: {'reg': Register.INVERTER_TEMP},
        0x000006a4: {'reg': Register.PV1_VOLTAGE},
        0x00000708: {'reg': Register.PV1_CURRENT},
        0x0000076c: {'reg': Register.PV1_POWER},
        0x000007d0: {'reg': Register.PV2_VOLTAGE},
        0x00000834: {'reg': Register.PV2_CURRENT},
        0x00000898: {'reg': Register.PV2_POWER},
        0x000008fc: {'reg': Register.PV3_VOLTAGE},
        0x00000960: {'reg': Register.PV3_CURRENT},
        0x000009c4: {'reg': Register.PV3_POWER},
        0x00000a28: {'reg': Register.PV4_VOLTAGE},
        0x00000a8c: {'reg': Register.PV4_CURRENT},
        0x00000af0: {'reg': Register.PV4_POWER},
        0x00000c1c: {'reg': Register.PV1_DAILY_GENERATION},
        0x00000c80: {'reg': Register.PV1_TOTAL_GENERATION},
        0x00000ce4: {'reg': Register.PV2_DAILY_GENERATION},
        0x00000d48: {'reg': Register.PV2_TOTAL_GENERATION},
        0x00000dac: {'reg': Register.PV3_DAILY_GENERATION},
        0x00000e10: {'reg': Register.PV3_TOTAL_GENERATION},
        0x00000e74: {'reg': Register.PV4_DAILY_GENERATION},
        0x00000ed8: {'reg': Register.PV4_TOTAL_GENERATION},
        0x00000b54: {'reg': Register.DAILY_GENERATION},
        0x00000bb8: {'reg': Register.TOTAL_GENERATION},
        0x000003e8: {'reg': Register.GRID_VOLTAGE},
        0x0000044c: {'reg': Register.GRID_CURRENT},
        0x000004b0: {'reg': Register.GRID_FREQUENCY},

        0x00000190: {'reg': Register.EVENT_ALARM},
        0x000001f4: {'reg': Register.EVENT_FAULT},
        0x00000258: {'reg': Register.EVENT_BF1},
        0x000002bc: {'reg': Register.EVENT_BF2},
        0x00000064: {'reg': Register.INVERTER_STATUS},

        0x00000fa0: {'reg': Register.BOOT_STATUS},
        0x00001004: {'reg': Register.DSP_STATUS},
        0x000010cc: {'reg': Register.WORK_MODE},
        0x000011f8: {'reg': Register.OUTPUT_SHUTDOWN},
        0x0000125c: {'reg': Register.MAX_DESIGNED_POWER},
        0x000012c0: {'reg': Register.RATED_LEVEL},
        0x00001324: {'reg': Register.INPUT_COEFFICIENT, 'ratio':  100/1024},
        0x00001388: {'reg': Register.GRID_VOLT_CAL_COEF},
        0x00002710: {'reg': Register.PROD_COMPL_TYPE},
        0x00003200: {'reg': Register.OUTPUT_COEFFICIENT, 'ratio':  100/1024},
    }


class RegisterSel:
    __sensor_map = {
            0x0e100000: RegisterMap.map_0e100000,
            0x01900000: RegisterMap.map_01900000,
            0x01900001: RegisterMap.map_01900001,
    }

    @classmethod
    def get(cls, sensor: int):
        return cls.__sensor_map.get(sensor, RegisterMap.map)


class InfosG3(Infos):
    __slots__ = ()

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
        # sensor = self.get_db_value(Register.SENSOR_LIST)
        # if "01900001" == sensor:
        items = RegisterMap.map_01900001.items()
        # else:
        #    items = {}

        for _, row in chain(RegisterMap.map_0e100000.items(), items):
            reg = row['reg']
            res = self.ha_conf(reg, ha_prfx, node_id, snr, False, sug_area)  # noqa: E501
            if res:
                yield res

    def parse(self, buf, ind=0, sensor: int = 0, node_id: str = '') -> \
            Generator[tuple[str, bool], None, None]:
        '''parse a data sequence received from the inverter and
        stores the values in Infos.db

        buf: buffer of the sequence to parse'''
        map = RegisterSel.get(sensor)
        result = struct.unpack_from('!l', buf, ind)
        elms = result[0]
        i = 0
        ind += 4
        while i < elms:
            result = struct.unpack_from('!lB', buf, ind)
            addr = result[0]
            if addr not in map:
                row = None
                info_id = -1
            else:
                row = map[addr]
                info_id = row['reg']
            data_type = result[1]
            ind += 5

            if data_type == 0x54:   # 'T' -> Pascal-String
                str_len = buf[ind]
                result = struct.unpack_from(f'!{str_len+1}p', buf,
                                            ind)[0].decode(encoding='ascii',
                                                           errors='replace')
                ind += str_len+1

            elif data_type == 0x00:  # 'Nul' -> end
                i = elms  # abort the loop

            elif data_type == 0x41:  # 'A' -> Nop ??
                ind += 0
                i += 1
                continue

            elif data_type == 0x42:  # 'B' -> byte, int8
                result = struct.unpack_from('!B', buf, ind)[0]
                ind += 1

            elif data_type == 0x49:  # 'I' -> int32
                result = struct.unpack_from('!l', buf, ind)[0]
                ind += 4

            elif data_type == 0x53:  # 'S' -> short, int16
                result = struct.unpack_from('!h', buf, ind)[0]
                ind += 2

            elif data_type == 0x46:  # 'F' -> float32
                result = round(struct.unpack_from('!f', buf, ind)[0], 2)
                ind += 4

            elif data_type == 0x4c:  # 'L' -> long, int64
                result = struct.unpack_from('!q', buf, ind)[0]
                ind += 8

            else:
                self.inc_counter('Invalid_Data_Type')
                logging.error(f"Infos.parse: data_type: {data_type}"
                              f" @0x{addr:04x} No:{i}"
                              " not supported")
                return

            result = self.__modify_val(row, result)

            yield from self.__store_result(addr, result, info_id, node_id)
            i += 1

    def __modify_val(self, row, result):
        if row and 'ratio' in row:
            result = round(result * row['ratio'], 2)
        return result

    def __store_result(self, addr, result, info_id, node_id):
        keys, level, unit, must_incr = self._key_obj(info_id)
        if keys:
            name, update = self.update_db(keys, must_incr, result)
            yield keys[0], update
        else:
            update = False
            name = str(f'info-id.0x{addr:x}')
        if update:
            self.tracer.log(level, f'[{node_id}] GEN3: {name} :'
                                   f' {result}{unit}')
