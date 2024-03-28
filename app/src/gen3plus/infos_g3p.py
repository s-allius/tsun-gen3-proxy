
import struct
import json
import logging
from typing import Generator

if __name__ == "app.src.gen3plus.infos_g3p":
    from app.src.infos import Infos
else:  # pragma: no cover
    from infos import Infos


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
        tab = self.info_defs
        for key in tab:
            row = tab[key]
            if 'singleton' in row:
                if singleton != row['singleton']:
                    continue
            elif singleton:
                continue
            prfx = ha_prfx + node_id

            # check if we have details for home assistant
            if 'ha' in row:
                ha = row['ha']
                if 'comp' in ha:
                    component = ha['comp']
                else:
                    component = 'sensor'
                attr = {}
                if 'name' in ha:
                    attr['name'] = ha['name']
                else:
                    attr['name'] = row['name'][-1]

                attr['stat_t'] = prfx + row['name'][0]
                attr['dev_cla'] = ha['dev_cla']
                attr['stat_cla'] = ha['stat_cla']
                attr['uniq_id'] = ha['id']+snr
                if 'val_tpl' in ha:
                    attr['val_tpl'] = ha['val_tpl']
                elif 'fmt' in ha:
                    attr['val_tpl'] = '{{value_json' + f"['{row['name'][-1]}'] {ha['fmt']}" + '}}'       # eg.   'val_tpl': "{{ value_json['Output_Power']|float }} # noqa: E501
                else:
                    self.inc_counter('Internal_Error')
                    logging.error(f"Infos._info_defs: the row for {key} do"
                                  " not have a 'val_tpl' nor a 'fmt' value")

                # add unit_of_meas only, if status_class isn't none. If
                # status_cla is None we want a number format and not line
                # graph in home assistant. A unit will change the number
                # format to a line graph
                if 'unit' in row and attr['stat_cla'] is not None:
                    attr['unit_of_meas'] = row['unit']  # 'unit_of_meas'
                if 'icon' in ha:
                    attr['ic'] = ha['icon']             # icon for the entity
                if 'nat_prc' in ha:
                    attr['sug_dsp_prc'] = ha['nat_prc']  # precison of floats
                if 'ent_cat' in ha:
                    attr['ent_cat'] = ha['ent_cat']     # diagnostic, config

                # enabled_by_default is deactivated, since it avoid the via
                # setup of the devices. It seems, that there is a bug in home
                # assistant. tested with 'Home Assistant 2023.10.4'
                # if 'en' in ha:                       # enabled_by_default
                #    attr['en'] = ha['en']

                if 'dev' in ha:
                    device = self.info_devs[ha['dev']]

                    if 'dep' in device and self.ignore_this_device(device['dep']):  # noqa: E501
                        continue

                    dev = {}

                    # the same name for 'name' and 'suggested area', so we get
                    # dedicated devices in home assistant with short value
                    # name and headline
                    if (sug_area == '' or
                            ('singleton' in device and device['singleton'])):
                        dev['name'] = device['name']
                        dev['sa'] = device['name']
                    else:
                        dev['name'] = device['name']+' - '+sug_area
                        dev['sa'] = device['name']+' - '+sug_area

                    if 'via' in device:  # add the link to the parent device
                        via = device['via']
                        if via in self.info_devs:
                            via_dev = self.info_devs[via]
                            if 'singleton' in via_dev and via_dev['singleton']:
                                dev['via_device'] = via
                            else:
                                dev['via_device'] = f"{via}_{snr}"
                        else:
                            self.inc_counter('Internal_Error')
                            logging.error(f"Infos._info_defs: the row for "
                                          f"{key} has an invalid via value: "
                                          f"{via}")

                    for key in ('mdl', 'mf', 'sw', 'hw'):      # add optional
                        # values fpr 'modell', 'manufacturer', 'sw version' and
                        # 'hw version'
                        if key in device:
                            data = self.dev_value(device[key])
                            if data is not None:
                                dev[key] = data

                    if 'singleton' in device and device['singleton']:
                        dev['ids'] = [f"{ha['dev']}"]
                    else:
                        dev['ids'] = [f"{ha['dev']}_{snr}"]

                    attr['dev'] = dev

                    origin = {}
                    origin['name'] = self.app_name
                    origin['sw'] = self.version
                    attr['o'] = origin
                else:
                    self.inc_counter('Internal_Error')
                    logging.error(f"Infos._info_defs: the row for {key} "
                                  "missing 'dev' value for ha register")

                yield json.dumps(attr), component, node_id, attr['uniq_id']

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
