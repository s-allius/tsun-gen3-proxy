import json
import os

# Dieses file übernimmt die Add-On Konfiguration und schreibt sie in die
# Konfigurationsdatei des tsun-proxy
# Die Addon Konfiguration wird in der Datei /data/options.json bereitgestellt
# Die Konfiguration wird in der Datei /home/proxy/config/config.toml
# gespeichert

# Übernehme die Umgebungsvariablen
# alternativ kann auch auf die homeassistant supervisor API zugegriffen werden

data = {}
data['mqtt.host'] = os.getenv('MQTT_HOST')
data['mqtt.port'] = os.getenv('MQTT_PORT')
data['mqtt.user'] = os.getenv('MQTT_USER')
data['mqtt.passwd'] = os.getenv('MQTT_PASSWORD')


# Lese die Add-On Konfiguration aus der Datei /data/options.json
with open('/data/options.json') as json_file:
    # with open('options.json') as json_file:
    options_data = json.load(json_file)
    data.update(options_data)


# Schreibe die Add-On Konfiguration in die Datei /home/proxy/config/config.toml    # noqa: E501
with open('/home/proxy/config/config.toml', 'w+') as f:
    # with open('./config/config.toml', 'w+') as f:
    f.write(f"""
mqtt.host    = '{data.get('mqtt.host')}' # URL or IP address of the mqtt broker
mqtt.port    = {data.get('mqtt.port')}
mqtt.user    = '{data.get('mqtt.user')}'
mqtt.passwd  = '{data.get('mqtt.passwd')}'


ha.auto_conf_prefix = '{data.get('ha.auto_conf_prefix', 'homeassistant')}'     # MQTT prefix for subscribing for homeassistant status updates    # noqa: E501
ha.discovery_prefix = '{data.get('ha.discovery_prefix', 'homeassistant')}'     # MQTT prefix for discovery topic                                 # noqa: E501
ha.entity_prefix    = '{data.get('ha.entity_prefix', 'tsun')}'              # MQTT topic prefix for publishing inverter values                   # noqa: E501
ha.proxy_node_id    = '{data.get('ha.proxy_node_id', 'proxy')}'             # MQTT node id, for the proxy_node_id
ha.proxy_unique_id  = '{data.get('ha.proxy_unique_id', 'P170000000000001')}'  # MQTT unique id, to identify a proxy instance


tsun.enabled = {str(data.get('tsun.enabled', True)).lower()}
tsun.host    = '{data.get('tsun.host', 'logger.talent-monitoring.com')}'
tsun.port    = {data.get('tsun.port', 5005)}


solarman.enabled = {str(data.get('solarman.enabled', True)).lower()}
solarman.host    = '{data.get('solarman.host', 'iot.talent-monitoring.com')}'
solarman.port    = {data.get('solarman.port', 10000)}


inverters.allow_all = {str(data.get('inverters.allow_all', False)).lower()}
""")

    for inverter in data['inverters']:
        f.write(f"""
[inverters."{inverter['serial']}"]
node_id = '{inverter['node_id']}'
suggested_area = '{inverter['suggested_area']}'
modbus_polling = {str(inverter['modbus_polling']).lower()}
pv1 = {{type = '{inverter['pv1_type']}', manufacturer = '{inverter['pv1_manufacturer']}'}}   # Optional, PV module descr    # noqa: E501
pv2 = {{type = '{inverter['pv2_type']}', manufacturer = '{inverter['pv2_manufacturer']}'}}   # Optional, PV module descr    # noqa: E501
""")
