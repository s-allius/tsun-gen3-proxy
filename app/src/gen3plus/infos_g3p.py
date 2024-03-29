
import struct
import logging
from typing import Generator

if __name__ == "app.src.gen3plus.infos_g3p":
    from app.src.infos import Infos, Register
else:  # pragma: no cover
    from infos import Infos, Register


class RegisterMap:
    map = {
        0x00092ba8: Register.COLLECTOR_FW_VERSION,
    }


class InfosG3P(Infos):
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
            info_id = result[0]
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
