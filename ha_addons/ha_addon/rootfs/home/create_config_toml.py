import json
import os

# Dieses file übernimmt die Add-On Konfiguration und schreibt sie in die
# Konfigurationsdatei des tsun-proxy
# Die Addon Konfiguration wird in der Datei /data/options.json bereitgestellt
# Die Konfiguration wird in der Datei /home/proxy/config/config.toml
# gespeichert

# Übernehme die Umgebungsvariablen
# alternativ kann auch auf die homeassistant supervisor API zugegriffen werden


def create_config():
    data = {}
    data['mqtt.host'] = os.getenv('MQTT_HOST', "mqtt")
    data['mqtt.port'] = os.getenv('MQTT_PORT', 1883)
    data['mqtt.user'] = os.getenv('MQTT_USER', "")
    data['mqtt.passwd'] = os.getenv('MQTT_PASSWORD', "")

    # Lese die Add-On Konfiguration aus der Datei /data/options.json
    # with open('data/options.json') as json_file:
    with open('/data/options.json') as json_file:
        try:
            options_data = json.load(json_file)
            data.update(options_data)
        except json.JSONDecodeError:
            pass

    # Schreibe die Add-On Konfiguration in die Datei /home/proxy/config/config.toml    # noqa: E501
    # with open('./config/config.toml', 'w+') as f:
    with open('/home/proxy/config/config.toml', 'w+') as f:
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

        if 'inverters' in data:
            for inverter in data['inverters']:
                f.write(f"""
[inverters."{inverter['serial']}"]
node_id = '{inverter['node_id']}'
suggested_area = '{inverter['suggested_area']}'
modbus_polling = {str(inverter['modbus_polling']).lower()}

# check if inverter has monitor_sn key. if not, skip monitor_sn
{f"monitor_sn = '{inverter['monitor_sn']}'" if 'monitor_sn' in inverter else ''}



# check if inverter has 'pv1_type' and 'pv1_manufacturer' keys. if not, skip pv1
{f"pv1 = {{type = '{inverter['pv1_type']}', manufacturer = '{inverter['pv1_manufacturer']}'}}" if 'pv1_type' in inverter and 'pv1_manufacturer' in inverter else ''}
# check if inverter has 'pv2_type' and 'pv2_manufacturer' keys. if not, skip pv2
{f"pv2 = {{type = '{inverter['pv2_type']}', manufacturer = '{inverter['pv2_manufacturer']}'}}" if 'pv2_type' in inverter and 'pv2_manufacturer' in inverter else ''}
# check if inverter has 'pv3_type' and 'pv3_manufacturer' keys. if not, skip pv3
{f"pv3 = {{type = '{inverter['pv3_type']}', manufacturer = '{inverter['pv3_manufacturer']}'}}" if 'pv3_type' in inverter and 'pv3_manufacturer' in inverter else ''}
# check if inverter has 'pv4_type' and 'pv4_manufacturer' keys. if not, skip pv4
{f"pv4 = {{type = '{inverter['pv4_type']}', manufacturer = '{inverter['pv4_manufacturer']}'}}" if 'pv4_type' in inverter and 'pv4_manufacturer' in inverter else ''}
# check if inverter has 'pv5_type' and 'pv5_manufacturer' keys. if not, skip pv5
{f"pv5 = {{type = '{inverter['pv5_type']}', manufacturer = '{inverter['pv5_manufacturer']}'}}" if 'pv5_type' in inverter and 'pv5_manufacturer' in inverter else ''}
# check if inverter has 'pv6_type' and 'pv6_manufacturer' keys. if not, skip pv6
{f"pv6 = {{type = '{inverter['pv6_type']}', manufacturer = '{inverter['pv6_manufacturer']}'}}" if 'pv6_type' in inverter and 'pv6_manufacturer' in inverter else ''}


""")

        # add filters
        f.write("""
[gen3plus.at_acl]
# filter for received commands from the internet
tsun.allow = [""")
        if 'gen3plus.at_acl.tsun.allow' in data:
            for rule in data['gen3plus.at_acl.tsun.allow']:
                f.write(f"'{rule}',")
        f.write("]\ntsun.block = [")
        if 'gen3plus.at_acl.tsun.block' in data:
            for rule in data['gen3plus.at_acl.tsun.block']:
                f.write(f"'{rule}',")
        f.write("""]
# filter for received commands from the MQTT broker
mqtt.allow = [""")
        if 'gen3plus.at_acl.mqtt.allow' in data:
            for rule in data['gen3plus.at_acl.mqtt.allow']:
                f.write(f"'{rule}',")
        f.write("]\nmqtt.block = [")
        if 'gen3plus.at_acl.mqtt.block' in data:
            for rule in data['gen3plus.at_acl.mqtt.block']:
                f.write(f"'{rule}',")
        f.write("]")


if __name__ == "__main__":
    create_config()
