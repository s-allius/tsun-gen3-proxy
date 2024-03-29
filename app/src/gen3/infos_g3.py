
import struct
import logging
from typing import Generator

if __name__ == "app.src.gen3.infos_g3":
    from app.src.infos import Infos, Register
else:  # pragma: no cover
    from infos import Infos, Register


class RegisterMap:
    map = {
        0x00092ba8: Register.COLLECTOR_FW_VERSION,
        0x000927c0: Register.CHIP_TYPE,
        0x00092f90: Register.CHIP_MODEL,
        0x00095a88: Register.TRACE_URL,
        0x00095aec: Register.LOGGER_URL,
        0x0000000a: Register.PRODUCT_NAME,
        0x00000014: Register.MANUFACTURER,
        0x0000001e: Register.VERSION,
        0x00000028: Register.SERIAL_NUMBER,
        0x00000032: Register.EQUIPMENT_MODEL,
        0x00013880: Register.NO_INPUTS,
        0xffffff00: Register.INVERTER_CNT,
        0xffffff01: Register.UNKNOWN_SNR,
        0xffffff02: Register.UNKNOWN_MSG,
        0xffffff03: Register.INVALID_DATA_TYPE,
        0xffffff04: Register.INTERNAL_ERROR,
        0xffffff05: Register.UNKNOWN_CTRL,
        0xffffff06: Register.OTA_START_MSG,
        0xffffff07: Register.SW_EXCEPTION,
        0xfffffffe: Register.TEST_REG1,
        0xffffffff: Register.TEST_REG2,
        0x00000640: Register.OUTPUT_POWER,
        0x000005dc: Register.RATED_POWER,
        0x00000514: Register.INVERTER_TEMP,
        0x000006a4: Register.PV1_VOLTAGE,
        0x00000708: Register.PV1_CURRENT,
        0x0000076c: Register.PV1_POWER,
        0x000007d0: Register.PV2_VOLTAGE,
        0x00000834: Register.PV2_CURRENT,
        0x00000898: Register.PV2_POWER,
        0x000008fc: Register.PV3_VOLTAGE,
        0x00000960: Register.PV3_CURRENT,
        0x000009c4: Register.PV3_POWER,
        0x00000a28: Register.PV4_VOLTAGE,
        0x00000a8c: Register.PV4_CURRENT,
        0x00000af0: Register.PV4_POWER,
        0x00000c1c: Register.PV1_DAILY_GENERATION,
        0x00000c80: Register.PV1_TOTAL_GENERATION,
        0x00000ce4: Register.PV2_DAILY_GENERATION,
        0x00000d48: Register.PV2_TOTAL_GENERATION,
        0x00000dac: Register.PV3_DAILY_GENERATION,
        0x00000e10: Register.PV3_TOTAL_GENERATION,
        0x00000e74: Register.PV4_DAILY_GENERATION,
        0x00000ed8: Register.PV4_TOTAL_GENERATION,
        0x00000b54: Register.DAILY_GENERATION,
        0x00000bb8: Register.TOTAL_GENERATION,
        0x000003e8: Register.GRID_VOLTAGE,
        0x0000044c: Register.GRID_CURRENT,
        0x000004b0: Register.GRID_FREQUENCY,
        0x000cfc38: Register.CONNECT_COUNT,
        0x000c3500: Register.SIGNAL_STRENGTH,
        0x000c96a8: Register.POWER_ON_TIME,
        0x000d0020: Register.COLLECT_INTERVAL,
        0x000cf850: Register.DATA_UP_INTERVAL,
        0x000c7f38: Register.COMMUNICATION_TYPE,
        0x00000191: Register.EVENT_401,
        0x00000192: Register.EVENT_402,
        0x00000193: Register.EVENT_403,
        0x00000194: Register.EVENT_404,
        0x00000195: Register.EVENT_405,
        0x00000196: Register.EVENT_406,
        0x00000197: Register.EVENT_407,
        0x00000198: Register.EVENT_408,
        0x00000199: Register.EVENT_409,
        0x0000019a: Register.EVENT_410,
        0x0000019b: Register.EVENT_411,
        0x0000019c: Register.EVENT_412,
        0x0000019d: Register.EVENT_413,
        0x0000019e: Register.EVENT_414,
        0x0000019f: Register.EVENT_415,
        0x000001a0: Register.EVENT_416,
    }


class InfosG3(Infos):

    def ha_confs(self, ha_prfx, node_id, snr,  singleton: bool, sug_area='') \
            -> Generator[tuple[dict, str], None, None]:
        '''Generator function yields a json register struct for home-assistant
        auto configuration and a unique entity string

        arguments:
        prfx:str     ==> MQTT prefix for the home assistant 'stat_t string
        snr:str      ==> serial number of the inverter, used to build unique
                         entity strings
        sug_area:str ==> suggested area string from the config file'''
        # iterate over RegisterMap.map and get the register values
        for key, reg in RegisterMap.map.items():
            if reg not in self.info_defs:
                continue
            row = self.info_defs[reg]
            res = self.ha_conf(row, reg, ha_prfx, node_id, snr, singleton, sug_area)  # noqa: E501
            if res:
                yield res

    def parse(self, buf, ind=0) -> Generator[tuple[str, bool], None, None]:
        '''parse a data sequence received from the inverter and
        stores the values in Infos.db

        buf: buffer of the sequence to parse'''
        result = struct.unpack_from('!l', buf, ind)
        elms = result[0]
        i = 0
        ind += 4
        while i < elms:
            result = struct.unpack_from('!lB', buf, ind)
            addr = result[0]
            if addr not in RegisterMap.map:
                info_id = -1
            else:
                info_id = RegisterMap.map[addr]
            data_type = result[1]
            ind += 5
            keys, level, unit, must_incr, new_val = self._key_obj(info_id)

            if data_type == 0x54:   # 'T' -> Pascal-String
                str_len = buf[ind]
                result = struct.unpack_from(f'!{str_len+1}p', buf,
                                            ind)[0].decode(encoding='ascii',
                                                           errors='replace')
                ind += str_len+1

            elif data_type == 0x49:  # 'I' -> int32
                # if new_val:
                #    struct.pack_into('!l', buf, ind, new_val)
                result = struct.unpack_from('!l', buf, ind)[0]
                ind += 4

            elif data_type == 0x53:  # 'S' -> short
                # if new_val:
                #     struct.pack_into('!h', buf, ind, new_val)
                result = struct.unpack_from('!h', buf, ind)[0]
                ind += 2

            elif data_type == 0x46:  # 'F' -> float32
                # if new_val:
                #     struct.pack_into('!f', buf, ind, new_val)
                result = round(struct.unpack_from('!f', buf, ind)[0], 2)
                ind += 4

            elif data_type == 0x4c:  # 'L' -> int64
                # if new_val:
                #     struct.pack_into('!q', buf, ind, new_val)
                result = struct.unpack_from('!q', buf, ind)[0]
                ind += 8

            else:
                self.inc_counter('Invalid_Data_Type')
                logging.error(f"Infos.parse: data_type: {data_type}"
                              " not supported")
                return

            if keys:
                dict = self.db
                name = ''

                for key in keys[:-1]:
                    if key not in dict:
                        dict[key] = {}
                    dict = dict[key]
                    name += key + '.'

                if keys[-1] not in dict:
                    update = (not must_incr or result > 0)
                else:
                    if must_incr:
                        update = dict[keys[-1]] < result
                    else:
                        update = dict[keys[-1]] != result

                if update:
                    dict[keys[-1]] = result
                name += keys[-1]
                yield keys[0], update
            else:
                update = False
                name = str(f'info-id.0x{info_id:x}')

            self.tracer.log(level, f'{name} : {result}{unit}'
                            f'  update: {update}')

            i += 1

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
