import struct
import json
import logging
import os


class Infos:
    stat = {}
    app_name = os.getenv('SERVICE_NAME', 'proxy')
    version = os.getenv('VERSION', 'unknown')

    @classmethod
    def static_init(cls):
        logging.info('Initialize proxy statistics')
        # init proxy counter in the class.stat dictionary
        cls.stat['proxy'] = {}
        for key in cls.__info_defs:
            name = cls.__info_defs[key]['name']
            if name[0] == 'proxy':
                cls.stat['proxy'][name[1]] = 0

        # add values from the environment to the device definition table
        prxy = cls.__info_devs['proxy']
        prxy['sw'] = cls.version
        prxy['mdl'] = cls.app_name

    def __init__(self):
        self.db = {}
        self.tracer = logging.getLogger('data')

    __info_devs = {
        'proxy':      {'singleton': True,   'name': 'Proxy', 'mf': 'Stefan Allius'},  # noqa: E501
        'controller': {'via': 'proxy',      'name': 'Controller',     'mdl': 0x00092f90, 'mf': 0x000927c0, 'sw': 0x00092ba8},  # noqa: E501
        'inverter':   {'via': 'controller', 'name': 'Micro Inverter', 'mdl': 0x00000032, 'mf': 0x00000014, 'sw': 0x0000001e},  # noqa: E501
        'input_pv1':  {'via': 'inverter',   'name': 'Module PV1'},
        'input_pv2':  {'via': 'inverter',   'name': 'Module PV2', 'dep': {'reg': 0x00013880, 'gte': 2}},  # noqa: E501
        'input_pv3':  {'via': 'inverter',   'name': 'Module PV3', 'dep': {'reg': 0x00013880, 'gte': 3}},  # noqa: E501
        'input_pv4':  {'via': 'inverter',   'name': 'Module PV4', 'dep': {'reg': 0x00013880, 'gte': 4}},  # noqa: E501
    }

    __comm_type_val_tpl = "{%set com_types = ['n/a','Wi-Fi', 'G4', 'G5', 'GPRS'] %}{{com_types[value_json['Communication_Type']|int(0)]|default(value_json['Communication_Type'])}}"    # noqa: E501

    __info_defs = {
        # collector values used for device registration:
        0x00092ba8:  {'name': ['collector', 'Collector_Fw_Version'],       'level': logging.INFO,  'unit': ''},  # noqa: E501
        0x000927c0:  {'name': ['collector', 'Chip_Type'],                  'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        0x00092f90:  {'name': ['collector', 'Chip_Model'],                 'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        0x00095a88:  {'name': ['collector', 'Trace_URL'],                  'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        0x00095aec:  {'name': ['collector', 'Logger_URL'],                 'level': logging.DEBUG, 'unit': ''},  # noqa: E501

        # inverter values used for device registration:
        0x0000000a:  {'name': ['inverter', 'Product_Name'],                'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        0x00000014:  {'name': ['inverter', 'Manufacturer'],                'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        0x0000001e:  {'name': ['inverter', 'Version'],                     'level': logging.INFO,  'unit': ''},  # noqa: E501
        0x00000028:  {'name': ['inverter', 'Serial_Number'],               'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        0x00000032:  {'name': ['inverter', 'Equipment_Model'],             'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        0x00013880:  {'name': ['inverter', 'No_Inputs'],                   'level': logging.DEBUG, 'unit': ''},  # noqa: E501

        # proxy:
        0xffffff00:  {'name': ['proxy', 'Inverter_Cnt'],       'singleton': True,   'ha': {'dev': 'proxy', 'comp': 'sensor', 'dev_cla': None, 'stat_cla': None, 'id': 'inv_count_',     'fmt': '| int', 'name': 'Active Inverter Connections',    'icon': 'mdi:counter'}},  # noqa: E501
        0xffffff01:  {'name': ['proxy', 'Unknown_SNR'],        'singleton': True,   'ha': {'dev': 'proxy', 'comp': 'sensor', 'dev_cla': None, 'stat_cla': None, 'id': 'unknown_snr_',   'fmt': '| int', 'name': 'Unknown Serial No',    'icon': 'mdi:counter', 'ent_cat': 'diagnostic'}},  # noqa: E501
        0xffffff02:  {'name': ['proxy', 'Unknown_Msg'],        'singleton': True,   'ha': {'dev': 'proxy', 'comp': 'sensor', 'dev_cla': None, 'stat_cla': None, 'id': 'unknown_msg_',   'fmt': '| int', 'name': 'Unknown Msg Type',     'icon': 'mdi:counter', 'ent_cat': 'diagnostic'}},  # noqa: E501
        0xffffff03:  {'name': ['proxy', 'Invalid_Data_Type'],  'singleton': True,   'ha': {'dev': 'proxy', 'comp': 'sensor', 'dev_cla': None, 'stat_cla': None, 'id': 'inv_data_type_', 'fmt': '| int', 'name': 'Invalid Data Type',    'icon': 'mdi:counter', 'ent_cat': 'diagnostic'}},  # noqa: E501
        0xffffff04:  {'name': ['proxy', 'Internal_Error'],     'singleton': True,   'ha': {'dev': 'proxy', 'comp': 'sensor', 'dev_cla': None, 'stat_cla': None, 'id': 'intern_err_',    'fmt': '| int', 'name': 'Internal Error',       'icon': 'mdi:counter', 'ent_cat': 'diagnostic', 'en': False}},  # noqa: E501
        0xffffff05:  {'name': ['proxy', 'Unknown_Ctrl'],       'singleton': True,   'ha': {'dev': 'proxy', 'comp': 'sensor', 'dev_cla': None, 'stat_cla': None, 'id': 'unknown_ctrl_',  'fmt': '| int', 'name': 'Unknown Control Type', 'icon': 'mdi:counter', 'ent_cat': 'diagnostic'}},  # noqa: E501
        0xffffff06:  {'name': ['proxy', 'OTA_Start_Msg'],      'singleton': True,   'ha': {'dev': 'proxy', 'comp': 'sensor', 'dev_cla': None, 'stat_cla': None, 'id': 'ota_start_cmd_', 'fmt': '| int', 'name': 'OTA Start Cmd',        'icon': 'mdi:counter', 'ent_cat': 'diagnostic'}},  # noqa: E501
        # 0xffffff03:  {'name':['proxy', 'Voltage'],                        'level': logging.DEBUG, 'unit': 'V',    'ha':{'dev':'proxy', 'dev_cla': 'voltage',     'stat_cla': 'measurement', 'id':'proxy_volt_',  'fmt':'| float','name': 'Grid Voltage'}},  # noqa: E501

        # events
        0x00000191:  {'name': ['events', '401_'],                          'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        0x00000192:  {'name': ['events', '402_'],                          'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        0x00000193:  {'name': ['events', '403_'],                          'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        0x00000194:  {'name': ['events', '404_'],                          'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        0x00000195:  {'name': ['events', '405_'],                          'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        0x00000196:  {'name': ['events', '406_'],                          'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        0x00000197:  {'name': ['events', '407_'],                          'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        0x00000198:  {'name': ['events', '408_'],                          'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        0x00000199:  {'name': ['events', '409_'],                          'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        0x0000019a:  {'name': ['events', '410_'],                          'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        0x0000019b:  {'name': ['events', '411_'],                          'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        0x0000019c:  {'name': ['events', '412_'],                          'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        0x0000019d:  {'name': ['events', '413_'],                          'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        0x0000019e:  {'name': ['events', '414_'],                          'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        0x0000019f:  {'name': ['events', '415_GridFreqOverRating'],        'level': logging.DEBUG, 'unit': ''},  # noqa: E501
        0x000001a0:  {'name': ['events', '416_'],                          'level': logging.DEBUG, 'unit': ''},  # noqa: E501

        # grid measures:
        0x000003e8:  {'name': ['grid', 'Voltage'],                         'level': logging.DEBUG, 'unit': 'V',    'ha': {'dev': 'inverter', 'dev_cla': 'voltage',     'stat_cla': 'measurement', 'id': 'out_volt_',  'fmt': '| float', 'name': 'Grid Voltage', 'ent_cat': 'diagnostic'}},  # noqa: E501
        0x0000044c:  {'name': ['grid', 'Current'],                         'level': logging.DEBUG, 'unit': 'A',    'ha': {'dev': 'inverter', 'dev_cla': 'current',     'stat_cla': 'measurement', 'id': 'out_cur_',   'fmt': '| float', 'name': 'Grid Current', 'ent_cat': 'diagnostic'}},  # noqa: E501
        0x000004b0:  {'name': ['grid', 'Frequency'],                       'level': logging.DEBUG, 'unit': 'Hz',   'ha': {'dev': 'inverter', 'dev_cla': 'frequency',   'stat_cla': 'measurement', 'id': 'out_freq_',  'fmt': '| float', 'name': 'Grid Frequency', 'ent_cat': 'diagnostic'}},  # noqa: E501
        0x00000640:  {'name': ['grid', 'Output_Power'],                    'level': logging.INFO,  'unit': 'W',    'ha': {'dev': 'inverter', 'dev_cla': 'power',       'stat_cla': 'measurement', 'id': 'out_power_', 'fmt': '| float', 'name': 'Power'}},  # noqa: E501
        0x000005dc:  {'name': ['env',  'Rated_Power'],                     'level': logging.DEBUG, 'unit': 'W',    'ha': {'dev': 'inverter', 'dev_cla': None,          'stat_cla': None,          'id': 'rated_power_', 'fmt': '| int', 'name': 'Rated Power', 'ent_cat': 'diagnostic'}},  # noqa: E501
        0x00000514:  {'name': ['env',  'Inverter_Temp'],                   'level': logging.DEBUG, 'unit': '°C',   'ha': {'dev': 'inverter', 'dev_cla': 'temperature', 'stat_cla': 'measurement', 'id': 'temp_',       'fmt': '| int', 'name': 'Temperature'}},  # noqa: E501

        # input measures:
        0x000006a4:  {'name': ['input', 'pv1', 'Voltage'],                 'level': logging.DEBUG, 'unit': 'V',    'ha': {'dev': 'input_pv1', 'dev_cla': 'voltage', 'stat_cla': 'measurement', 'id': 'volt_pv1_',  'val_tpl': "{{ (value_json['pv1']['Voltage'] | float)}}", 'icon': 'mdi:gauge', 'ent_cat': 'diagnostic'}},  # noqa: E501
        0x00000708:  {'name': ['input', 'pv1', 'Current'],                 'level': logging.DEBUG, 'unit': 'A',    'ha': {'dev': 'input_pv1', 'dev_cla': 'current', 'stat_cla': 'measurement', 'id': 'cur_pv1_',   'val_tpl': "{{ (value_json['pv1']['Current'] | float)}}", 'icon': 'mdi:gauge', 'ent_cat': 'diagnostic'}},  # noqa: E501
        0x0000076c:  {'name': ['input', 'pv1', 'Power'],                   'level': logging.INFO,  'unit': 'W',    'ha': {'dev': 'input_pv1', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'power_pv1_', 'val_tpl': "{{ (value_json['pv1']['Power'] | float)}}"}},  # noqa: E501
        0x000007d0:  {'name': ['input', 'pv2', 'Voltage'],                 'level': logging.DEBUG, 'unit': 'V',    'ha': {'dev': 'input_pv2', 'dev_cla': 'voltage', 'stat_cla': 'measurement', 'id': 'volt_pv2_',  'val_tpl': "{{ (value_json['pv2']['Voltage'] | float)}}", 'icon': 'mdi:gauge', 'ent_cat': 'diagnostic'}},  # noqa: E501
        0x00000834:  {'name': ['input', 'pv2', 'Current'],                 'level': logging.DEBUG, 'unit': 'A',    'ha': {'dev': 'input_pv2', 'dev_cla': 'current', 'stat_cla': 'measurement', 'id': 'cur_pv2_',   'val_tpl': "{{ (value_json['pv2']['Current'] | float)}}", 'icon': 'mdi:gauge', 'ent_cat': 'diagnostic'}},  # noqa: E501
        0x00000898:  {'name': ['input', 'pv2', 'Power'],                   'level': logging.INFO,  'unit': 'W',    'ha': {'dev': 'input_pv2', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'power_pv2_', 'val_tpl': "{{ (value_json['pv2']['Power'] | float)}}"}},  # noqa: E501
        0x000008fc:  {'name': ['input', 'pv3', 'Voltage'],                 'level': logging.DEBUG, 'unit': 'V',    'ha': {'dev': 'input_pv3', 'dev_cla': 'voltage', 'stat_cla': 'measurement', 'id': 'volt_pv3_',  'val_tpl': "{{ (value_json['pv3']['Voltage'] | float)}}", 'icon': 'mdi:gauge', 'ent_cat': 'diagnostic'}},  # noqa: E501
        0x00000960:  {'name': ['input', 'pv3', 'Current'],                 'level': logging.DEBUG, 'unit': 'A',    'ha': {'dev': 'input_pv3', 'dev_cla': 'current', 'stat_cla': 'measurement', 'id': 'cur_pv3_',   'val_tpl': "{{ (value_json['pv3']['Current'] | float)}}", 'icon': 'mdi:gauge', 'ent_cat': 'diagnostic'}},  # noqa: E501
        0x000009c4:  {'name': ['input', 'pv3', 'Power'],                   'level': logging.DEBUG, 'unit': 'W',    'ha': {'dev': 'input_pv3', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'power_pv3_', 'val_tpl': "{{ (value_json['pv3']['Power'] | float)}}"}},  # noqa: E501
        0x00000a28:  {'name': ['input', 'pv4', 'Voltage'],                 'level': logging.DEBUG, 'unit': 'V',    'ha': {'dev': 'input_pv4', 'dev_cla': 'voltage', 'stat_cla': 'measurement', 'id': 'volt_pv4_',  'val_tpl': "{{ (value_json['pv4']['Voltage'] | float)}}", 'icon': 'mdi:gauge', 'ent_cat': 'diagnostic'}},  # noqa: E501
        0x00000a8c:  {'name': ['input', 'pv4', 'Current'],                 'level': logging.DEBUG, 'unit': 'A',    'ha': {'dev': 'input_pv4', 'dev_cla': 'current', 'stat_cla': 'measurement', 'id': 'cur_pv4_',   'val_tpl': "{{ (value_json['pv4']['Current'] | float)}}", 'icon': 'mdi:gauge', 'ent_cat': 'diagnostic'}},  # noqa: E501
        0x00000af0:  {'name': ['input', 'pv4', 'Power'],                   'level': logging.DEBUG, 'unit': 'W',    'ha': {'dev': 'input_pv4', 'dev_cla': 'power',   'stat_cla': 'measurement', 'id': 'power_pv4_', 'val_tpl': "{{ (value_json['pv4']['Power'] | float)}}"}},  # noqa: E501
        0x00000c1c:  {'name': ['input', 'pv1', 'Daily_Generation'],        'level': logging.DEBUG, 'unit': 'kWh',  'ha': {'dev': 'input_pv1', 'dev_cla': 'energy', 'stat_cla': 'total_increasing', 'id': 'daily_gen_pv1_', 'name': 'Daily Generation', 'val_tpl': "{{ (value_json['pv1']['Daily_Generation'] | float)}}", 'icon': 'mdi:solar-power-variant', 'must_incr': True}},  # noqa: E501
        0x00000c80:  {'name': ['input', 'pv1', 'Total_Generation'],        'level': logging.DEBUG, 'unit': 'kWh',  'ha': {'dev': 'input_pv1', 'dev_cla': 'energy', 'stat_cla': 'total',            'id': 'total_gen_pv1_', 'name': 'Total Generation', 'val_tpl': "{{ (value_json['pv1']['Total_Generation'] | float)}}", 'icon': 'mdi:solar-power', 'must_incr': True}},  # noqa: E501
        0x00000ce4:  {'name': ['input', 'pv2', 'Daily_Generation'],        'level': logging.DEBUG, 'unit': 'kWh',  'ha': {'dev': 'input_pv2', 'dev_cla': 'energy', 'stat_cla': 'total_increasing', 'id': 'daily_gen_pv2_', 'name': 'Daily Generation', 'val_tpl': "{{ (value_json['pv2']['Daily_Generation'] | float)}}", 'icon': 'mdi:solar-power-variant', 'must_incr': True}},  # noqa: E501
        0x00000d48:  {'name': ['input', 'pv2', 'Total_Generation'],        'level': logging.DEBUG, 'unit': 'kWh',  'ha': {'dev': 'input_pv2', 'dev_cla': 'energy', 'stat_cla': 'total',            'id': 'total_gen_pv2_', 'name': 'Total Generation', 'val_tpl': "{{ (value_json['pv2']['Total_Generation'] | float)}}", 'icon': 'mdi:solar-power', 'must_incr': True}},  # noqa: E501
        0x00000dac:  {'name': ['input', 'pv3', 'Daily_Generation'],        'level': logging.DEBUG, 'unit': 'kWh',  'ha': {'dev': 'input_pv3', 'dev_cla': 'energy', 'stat_cla': 'total_increasing', 'id': 'daily_gen_pv3_', 'name': 'Daily Generation', 'val_tpl': "{{ (value_json['pv3']['Daily_Generation'] | float)}}", 'icon': 'mdi:solar-power-variant', 'must_incr': True}},  # noqa: E501
        0x00000e10:  {'name': ['input', 'pv3', 'Total_Generation'],        'level': logging.DEBUG, 'unit': 'kWh',  'ha': {'dev': 'input_pv3', 'dev_cla': 'energy', 'stat_cla': 'total',            'id': 'total_gen_pv3_', 'name': 'Total Generation', 'val_tpl': "{{ (value_json['pv3']['Total_Generation'] | float)}}", 'icon': 'mdi:solar-power', 'must_incr': True}},  # noqa: E501
        0x00000e74:  {'name': ['input', 'pv4', 'Daily_Generation'],        'level': logging.DEBUG, 'unit': 'kWh',  'ha': {'dev': 'input_pv4', 'dev_cla': 'energy', 'stat_cla': 'total_increasing', 'id': 'daily_gen_pv4_', 'name': 'Daily Generation', 'val_tpl': "{{ (value_json['pv4']['Daily_Generation'] | float)}}", 'icon': 'mdi:solar-power-variant', 'must_incr': True}},  # noqa: E501
        0x00000ed8:  {'name': ['input', 'pv4', 'Total_Generation'],        'level': logging.DEBUG, 'unit': 'kWh',  'ha': {'dev': 'input_pv4', 'dev_cla': 'energy', 'stat_cla': 'total',            'id': 'total_gen_pv4_', 'name': 'Total Generation', 'val_tpl': "{{ (value_json['pv4']['Total_Generation'] | float)}}", 'icon': 'mdi:solar-power', 'must_incr': True}},  # noqa: E501
        # total:
        0x00000b54:  {'name': ['total', 'Daily_Generation'],               'level': logging.INFO,  'unit': 'kWh',  'ha': {'dev': 'inverter', 'dev_cla': 'energy', 'stat_cla': 'total_increasing', 'id': 'daily_gen_', 'fmt': '| float', 'name': 'Daily Generation', 'icon': 'mdi:solar-power-variant', 'must_incr': True}},  # noqa: E501
        0x00000bb8:  {'name': ['total', 'Total_Generation'],               'level': logging.INFO,  'unit': 'kWh',  'ha': {'dev': 'inverter', 'dev_cla': 'energy', 'stat_cla': 'total',            'id': 'total_gen_', 'fmt': '| float', 'name': 'Total Generation', 'icon': 'mdi:solar-power', 'must_incr': True}},  # noqa: E501

        # controller:
        0x000c3500:  {'name': ['controller', 'Signal_Strength'],           'level': logging.DEBUG, 'unit': '%',    'ha': {'dev': 'controller', 'dev_cla': None,       'stat_cla': 'measurement', 'id': 'signal_',         'fmt': '| int', 'name': 'Signal Strength', 'icon': 'mdi:wifi'}},  # noqa: E501
        0x000c96a8:  {'name': ['controller', 'Power_On_Time'],             'level': logging.DEBUG, 'unit': 's',    'ha': {'dev': 'controller', 'dev_cla': 'duration', 'stat_cla': 'measurement', 'id': 'power_on_time_',       'name': 'Power on Time',   'val_tpl': "{{ (value_json['Power_On_Time'] | float)}}", 'nat_prc': '3', 'ent_cat': 'diagnostic'}},  # noqa: E501
        0x000d0020:  {'name': ['controller', 'Collect_Interval'],          'level': logging.DEBUG, 'unit': 's',    'ha': {'dev': 'controller', 'dev_cla': None,       'stat_cla': 'measurement', 'id': 'data_collect_intval_', 'fmt': '| int', 'name': 'Data Collect Interval', 'icon': 'mdi:update', 'ent_cat': 'diagnostic'}},  # noqa: E501
        0x000cfc38:  {'name': ['controller', 'Connect_Count'],             'level': logging.DEBUG, 'unit': 's',    'ha': {'dev': 'controller', 'comp': 'sensor', 'dev_cla': None, 'stat_cla': None, 'id': 'connect_count_',    'fmt': '| int', 'name': 'Connect Count',    'icon': 'mdi:counter'}},  # noqa: E501
        0x000c7f38:  {'name': ['controller', 'Communication_Type'],        'level': logging.DEBUG, 'unit': '',     'ha': {'dev': 'controller', 'comp': 'sensor', 'dev_cla': None, 'stat_cla': None, 'id': 'comm_type_',        'name': 'Communication Type', 'val_tpl': __comm_type_val_tpl, 'icon': 'mdi:wifi'}},  # noqa: E501
        # 0x000c7f38:  {'name': ['controller', 'Communication_Type'],        'level': logging.DEBUG, 'unit': 's',    'new_value': 5},  # noqa: E501
        0x000cf850:  {'name': ['controller', 'Data_Up_Interval'],          'level': logging.DEBUG, 'unit': 's',    'ha': {'dev': 'controller', 'dev_cla': None,       'stat_cla': 'measurement', 'id': 'data_up_intval_', 'fmt': '| int', 'name': 'Data Up Interval', 'icon': 'mdi:update', 'ent_cat': 'diagnostic'}},  # noqa: E501

    }

    def dev_value(self, idx: str | int) -> str | int | float | None:
        '''returns the stored device value from our database

        idx:int ==> lookup the value in the database and return it as str,
                    int or flout. If the value is not available return 'None'
        idx:str ==> returns the string as a fixed value without a
                    database loopup
        '''
        if type(idx) is str:
            return idx               # return idx as a fixed value
        elif idx in self.__info_defs:
            row = self.__info_defs[idx]
            if 'singleton' in row and row['singleton']:
                dict = self.stat
            else:
                dict = self.db

            keys = row['name']

            for key in keys:
                if key not in dict:
                    return None      # value not found in the database
                dict = dict[key]
            return dict              # value of the reqeusted entry

        return None                  # unknwon idx, not in __info_defs

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

    def ha_confs(self, ha_prfx, node_id, snr,  singleton: bool, sug_area=''):
        '''Generator function yields a json register struct for home-assistant
        auto configuration and a unique entity string

        arguments:
        prfx:str     ==> MQTT prefix for the home assistant 'stat_t string
        snr:str      ==> serial number of the inverter, used to build unique
                         entity strings
        sug_area:str ==> suggested area string from the config file'''
        tab = self.__info_defs
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
                    logging.error(f"Infos.__info_defs: the row for {key} do"
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
                    device = self.__info_devs[ha['dev']]

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
                        if via in self.__info_devs:
                            via_dev = self.__info_devs[via]
                            if 'singleton' in via_dev and via_dev['singleton']:
                                dev['via_device'] = via
                            else:
                                dev['via_device'] = f"{via}_{snr}"
                        else:
                            self.inc_counter('Internal_Error')
                            logging.error(f"Infos.__info_defs: the row for "
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
                    logging.error(f"Infos.__info_defs: the row for {key} "
                                  "missing 'dev' value for ha register")

                yield json.dumps(attr), component, node_id, attr['uniq_id']

    def inc_counter(self, counter: str) -> None:
        '''inc proxy statistic counter'''
        dict = self.stat['proxy']
        dict[counter] += 1

    def dec_counter(self, counter: str) -> None:
        '''dec proxy statistic counter'''
        dict = self.stat['proxy']
        dict[counter] -= 1

    def __key_obj(self, id) -> list:
        d = self.__info_defs.get(id, {'name': None, 'level': logging.DEBUG,
                                      'unit': ''})
        if 'ha' in d and 'must_incr' in d['ha']:
            must_incr = d['ha']['must_incr']
        else:
            must_incr = False
        new_val = None
        # if 'new_value' in d:
        #     new_val = d['new_value']

        return d['name'], d['level'], d['unit'], must_incr, new_val

    def parse(self, buf, ind=0) -> None:
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
            keys, level, unit, must_incr, new_val = self.__key_obj(info_id)

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
