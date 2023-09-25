import struct, json, logging



class Infos:    
    def __init__(self):
        self.db = {}
        self.tracer = logging.getLogger('data')

    __info_defs={
        # collector values:
            0x00092ba8:  {'name':['collector', 'Collector_Fw_Version'],       'level': logging.INFO,  'unit': ''},
            0x000927c0:  {'name':['collector', 'Chip_Type'],                  'level': logging.DEBUG, 'unit': ''},
            0x00092f90:  {'name':['collector', 'Chip_Model'],                 'level': logging.DEBUG, 'unit': ''},
            0x00095a88:  {'name':['collector', 'Trace_URL'],                  'level': logging.DEBUG, 'unit': ''},
            0x00095aec:  {'name':['collector', 'Logger_URL'],                 'level': logging.DEBUG, 'unit': ''},
            0x000cf850:  {'name':['collector', 'Data_Up_Interval'],           'level': logging.DEBUG, 'unit': 's'},
            0x000005dc:  {'name':['collector', 'Rated_Power'],                'level': logging.DEBUG, 'unit': 'W'},
        # inverter values:
            0x0000000a:  {'name':['inverter', 'Product_Name'],                'level': logging.DEBUG, 'unit': ''},
            0x00000014:  {'name':['inverter', 'Manufacturer'],                'level': logging.DEBUG, 'unit': ''},
            0x0000001e:  {'name':['inverter', 'Version'],                     'level': logging.INFO,  'unit': ''},
            0x00000028:  {'name':['inverter', 'Serial_Number'],               'level': logging.DEBUG, 'unit': ''},
            0x00000032:  {'name':['inverter', 'Equipment_Model'],             'level': logging.DEBUG, 'unit': ''},
        # env:
            0x00000514:  {'name':['env', 'Inverter_Temp'],                    'level': logging.DEBUG, 'unit': '°C',  'ha':{'dev_cla': 'temperature', 'stat_cla': 'measurement', 'id':'temp_',   'fmt':'| float','name': 'Inverter Temperature'}},
            0x000c3500:  {'name':['env', 'Signal_Strength'],                  'level': logging.DEBUG, 'unit': '%' ,  'ha':{'dev_cla': None,          'stat_cla': 'measurement', 'id':'signal_', 'fmt':'| float','name': 'Signal Strength', 'icon':'mdi:wifi'}},

        # events:
            0x00000191:  {'name':['events', '401_'],                          'level': logging.DEBUG, 'unit': ''},
            0x00000192:  {'name':['events', '402_'],                          'level': logging.DEBUG, 'unit': ''},
            0x00000193:  {'name':['events', '403_'],                          'level': logging.DEBUG, 'unit': ''},
            0x00000194:  {'name':['events', '404_'],                          'level': logging.DEBUG, 'unit': ''},
            0x00000195:  {'name':['events', '405_'],                          'level': logging.DEBUG, 'unit': ''},
            0x00000196:  {'name':['events', '406_'],                          'level': logging.DEBUG, 'unit': ''},
            0x00000197:  {'name':['events', '407_'],                          'level': logging.DEBUG, 'unit': ''},
            0x00000198:  {'name':['events', '408_'],                          'level': logging.DEBUG, 'unit': ''},
            0x00000199:  {'name':['events', '409_'],                          'level': logging.DEBUG, 'unit': ''},
            0x0000019a:  {'name':['events', '410_'],                          'level': logging.DEBUG, 'unit': ''},
            0x0000019b:  {'name':['events', '411_'],                          'level': logging.DEBUG, 'unit': ''},
            0x0000019c:  {'name':['events', '412_'],                          'level': logging.DEBUG, 'unit': ''},
            0x0000019d:  {'name':['events', '413_'],                          'level': logging.DEBUG, 'unit': ''},
            0x0000019e:  {'name':['events', '414_'],                          'level': logging.DEBUG, 'unit': ''},
            0x0000019f:  {'name':['events', '415_GridFreqOverRating'],        'level': logging.DEBUG, 'unit': ''},
            0x000001a0:  {'name':['events', '416_'],                          'level': logging.DEBUG, 'unit': ''},
        # grid measures:
            0x000003e8:  {'name':['grid', 'Voltage'],                         'level': logging.DEBUG, 'unit': 'V',    'ha':{'dev_cla': 'voltage',     'stat_cla': 'measurement', 'id':'out_volt_',  'fmt':'| float','name': 'Grid Voltage'}},
            0x0000044c:  {'name':['grid', 'Current'],                         'level': logging.DEBUG, 'unit': 'A',    'ha':{'dev_cla': 'current',     'stat_cla': 'measurement', 'id':'out_cur_',   'fmt':'| float','name': 'Grid Current'}},
            0x000004b0:  {'name':['grid', 'Frequency'],                       'level': logging.DEBUG, 'unit': 'Hz',   'ha':{'dev_cla': 'frequency',   'stat_cla': 'measurement', 'id':'out_freq_',  'fmt':'| float','name': 'Grid Frequency'}},
            0x00000640:  {'name':['grid', 'Output_Power'],                    'level': logging.INFO,  'unit': 'W',    'ha':{'dev_cla': 'power',       'stat_cla': 'measurement', 'id':'out_power_', 'fmt':'| float','name': 'Actual Power'}},
        # input measures:           
            0x000006a4:  {'name':['input', 'pv1', 'Voltage'],                 'level': logging.DEBUG, 'unit': 'V'},
            0x00000708:  {'name':['input', 'pv1', 'Current'],                 'level': logging.DEBUG, 'unit': 'A'},
            0x0000076c:  {'name':['input', 'pv1', 'Power'],                   'level': logging.INFO,  'unit': 'W',    'ha':{'dev_cla': 'power', 'stat_cla': 'measurement', 'id':'power_pv1_','name': 'Power PV1', 'val_tpl' :"{{ (value_json['pv1']['Power'] | float)}}"}},
            0x000007d0:  {'name':['input', 'pv2', 'Voltage'],                 'level': logging.DEBUG, 'unit': 'V'},
            0x00000834:  {'name':['input', 'pv2', 'Current'],                 'level': logging.DEBUG, 'unit': 'A'},
            0x00000898:  {'name':['input', 'pv2', 'Power'],                   'level': logging.INFO,  'unit': 'W',    'ha':{'dev_cla': 'power', 'stat_cla': 'measurement', 'id':'power_pv2_','name': 'Power PV2', 'val_tpl' :"{{ (value_json['pv2']['Power'] | float)}}"}},
            0x000008fc:  {'name':['input', 'pv3', 'Voltage'],                 'level': logging.DEBUG, 'unit': 'V'},
            0x00000960:  {'name':['input', 'pv3', 'Curent'],                  'level': logging.DEBUG, 'unit': 'A'},
            0x000009c4:  {'name':['input', 'pv3', 'Power'],                   'level': logging.DEBUG, 'unit': 'W',    'ha':{'dev_cla': 'power', 'stat_cla': 'measurement', 'id':'power_pv3_','name': 'Power PV3', 'val_tpl' :"{{ (value_json['pv3']['Power'] | float)}}"}},
            0x00000a28:  {'name':['input', 'pv4', 'Voltage'],                 'level': logging.DEBUG, 'unit': 'V'},
            0x00000a8c:  {'name':['input', 'pv4', 'Current'],                 'level': logging.DEBUG, 'unit': 'A'},
            0x00000af0:  {'name':['input', 'pv4', 'Power'],                   'level': logging.DEBUG, 'unit': 'W',    'ha':{'dev_cla': 'power', 'stat_cla': 'measurement', 'id':'power_pv4_','name': 'Power PV4', 'val_tpl' :"{{ (value_json['pv4']['Power'] | float)}}"}},
            0x00000c1c:  {'name':['input', 'pv1', 'Daily_Generation'],        'level': logging.DEBUG, 'unit': 'kWh',  'ha':{'dev_cla': 'energy', 'stat_cla': 'total_increasing', 'id':'daily_gen_pv1_','name': 'Daily Generation PV1', 'val_tpl' :"{{ (value_json['pv1']['Daily_Generation'] | float)}}"}},          
            0x00000c80:  {'name':['input', 'pv1', 'Total_Generation'],        'level': logging.DEBUG, 'unit': 'kWh',  'ha':{'dev_cla': 'energy', 'stat_cla': 'total',            'id':'total_gen_pv1_','name': 'Total Generation PV1', 'val_tpl' :"{{ (value_json['pv1']['Total_Generation'] | float)}}"}},                    
            0x00000ce4:  {'name':['input', 'pv2', 'Daily_Generation'],        'level': logging.DEBUG, 'unit': 'kWh',  'ha':{'dev_cla': 'energy', 'stat_cla': 'total_increasing', 'id':'daily_gen_pv2_','name': 'Daily Generation PV2', 'val_tpl' :"{{ (value_json['pv2']['Daily_Generation'] | float)}}"}},          
            0x00000d48:  {'name':['input', 'pv2', 'Total_Generation'],        'level': logging.DEBUG, 'unit': 'kWh',  'ha':{'dev_cla': 'energy', 'stat_cla': 'total',            'id':'total_gen_pv2_','name': 'Total Generation PV2', 'val_tpl' :"{{ (value_json['pv2']['Total_Generation'] | float)}}"}},          
            0x00000dac:  {'name':['input', 'pv3', 'Daily_Generation'],        'level': logging.DEBUG, 'unit': 'kWh',  'ha':{'dev_cla': 'energy', 'stat_cla': 'total_increasing', 'id':'daily_gen_pv3_','name': 'Daily Generation PV3', 'val_tpl' :"{{ (value_json['pv3']['Daily_Generation'] | float)}}"}},          
            0x00000e10:  {'name':['input', 'pv3', 'Total_Generation'],        'level': logging.DEBUG, 'unit': 'kWh',  'ha':{'dev_cla': 'energy', 'stat_cla': 'total',            'id':'total_gen_pv3_','name': 'Total Generation PV3', 'val_tpl' :"{{ (value_json['pv3']['Total_Generation'] | float)}}"}},                    
            0x00000e74:  {'name':['input', 'pv4', 'Daily_Generation'],        'level': logging.DEBUG, 'unit': 'kWh',  'ha':{'dev_cla': 'energy', 'stat_cla': 'total_increasing', 'id':'daily_gen_pv4_','name': 'Daily Generation PV4', 'val_tpl' :"{{ (value_json['pv4']['Daily_Generation'] | float)}}"}},          
            0x00000ed8:  {'name':['input', 'pv4', 'Total_Generation'],        'level': logging.DEBUG, 'unit': 'kWh',  'ha':{'dev_cla': 'energy', 'stat_cla': 'total',            'id':'total_gen_pv4_','name': 'Total Generation PV4', 'val_tpl' :"{{ (value_json['pv4']['Total_Generation'] | float)}}"}},          
        # total:    
            0x00000b54:  {'name':['total', 'Daily_Generation'],               'level': logging.INFO,  'unit': 'kWh',  'ha':{'dev_cla': 'energy', 'stat_cla': 'total_increasing', 'id':'daily_gen_', 'fmt':'| float','name': 'Daily Generation'}},
            0x00000bb8:  {'name':['total', 'Total_Generation'],               'level': logging.INFO,  'unit': 'kWh',  'ha':{'dev_cla': 'energy', 'stat_cla': 'total',            'id':'total_gen_', 'fmt':'| float','name': 'Total Generation', 'icon':'mdi:solar-power'}},
            0x000c96a8:  {'name':['total', 'Power_On_Time'],                  'level': logging.DEBUG, 'unit': 's',    'ha':{'dev_cla': 'duration',  'stat_cla': 'measurement',      'id':'power_on_time_',             'name': 'Power on Time', 'val_tpl':"{{ (value_json['Power_On_Time'] | float)}}", 'nat_prc':'3'}},

    }          
                                    
 
    def ha_confs(self, prfx="tsun/garagendach/", snr='123', sug_area =''):
        tab = self.__info_defs
        for key in tab:
            row = tab[key]
            if 'ha' in row:
                ha = row['ha']
                attr = {}
                if 'name' in ha:
                    attr['name']   = ha['name']               # eg.  'name': "Actual Power"
                else:                 
                    attr['name']   = row['name'][-1]          # eg.  'name': "Actual Power"

                attr['stat_t'] = prfx +row['name'][0]         # eg.  'stat_t': "tsun/garagendach/grid"
                attr['dev_cla']  = ha['dev_cla']              # eg.  'dev_cla': 'power'
                attr['stat_cla'] = ha['stat_cla']             # eg.  'stat_cla': "measurement"
                attr['uniq_id']  = ha['id']+snr               # eg.  'uniq_id':'out_power_123'
                if 'val_tpl' in ha:
                    attr['val_tpl']  = ha['val_tpl']       # eg.   'val_tpl': "{{ value_json['Output_Power']|float }}"
                elif 'fmt' in ha:
                    attr['val_tpl']  = '{{value_json' + f"['{row['name'][-1]}'] {ha['fmt']}" + '}}'       # eg.   'val_tpl': "{{ value_json['Output_Power']|float }}"

                if 'unit' in row:
                    attr['unit_of_meas'] = row['unit']        # eg.  'unit_of_meas': 'W'
                if 'icon' in ha:
                    attr['icon'] = ha['icon']                 # eg. 'icon':'mdi:solar-power'
                if 'nat_prc' in ha:
                    attr['suggested_display_precision'] = ha['nat_prc']       
                    
                # eg. 'dev':{'name':'Microinverter','mdl':'MS-600','ids':["inverter_123"],'mf':'TSUN','sa': 'auf Garagendach'}
                # attr['dev'] = {'name':'Microinverter','mdl':'MS-600','ids':[f'inverter_{snr}'],'mf':'TSUN','sa': 'auf Garagendach'}   
                dev = {}
                dev['name'] = 'Microinverter' #fixme
                dev['mdl']  = 'MS-600'        #fixme
                dev['ids']  = [f'inverter_{snr}']
                dev['mf']   = 'TSUN'          #fixme
                dev['sa']   = sug_area
                dev['sw']   = '0.01'          #fixme
                dev['hw']   = 'Hw0.01'        #fixme
                #dev['via_device'] =          #fixme
                attr['dev'] = dev
                

                yield json.dumps (attr), attr['uniq_id']
   


                                        
                                  
    
    def __key_obj(self, id) -> list:
        d = self.__info_defs.get(id, {'name': None, 'level': logging.DEBUG, 'unit': ''})
        return d['name'], d['level'], d['unit']
    
    
    def parse(self, buf):
        result = struct.unpack_from('!l', buf, 0)
        elms = result[0]
        i = 0
        ind = 4
        while i < elms:
            result = struct.unpack_from('!lB', buf, ind)
            info_id   = result[0]             
            data_type = result[1]
            ind += 5
            keys, level, unit = self.__key_obj(info_id)
            
            if data_type==0x54:   # 'T' -> Pascal-String
                str_len = buf[ind]
                result = struct.unpack_from(f'!{str_len+1}p', buf, ind)[0].decode(encoding='ascii', errors='replace')
                ind += str_len+1
            
            elif data_type==0x49: # 'I' -> int32
                result = struct.unpack_from(f'!l', buf, ind)[0]
                ind += 4

            elif data_type==0x53: # 'S' -> short
                result = struct.unpack_from(f'!h', buf, ind)[0]
                ind += 2

            elif data_type==0x46: # 'F' -> float32
                result = round(struct.unpack_from(f'!f', buf, ind)[0],2)
                ind += 4


            if keys:
                dict = self.db
                name = ''
            
                for key in keys[:-1]:
                    if key not in dict:
                        dict[key] = {}
                    dict = dict[key]
                    name += key + '.'

                update = keys[-1] not in dict or dict[keys[-1]] != result
                dict[keys[-1]] = result
                name += keys[-1]
                yield keys[0], update    
            else:
                update = False    
                name = str(f'info-id.0x{info_id:x}')
            
            self.tracer.log(level, f'{name} : {result}{unit}')
 
            i +=1

   