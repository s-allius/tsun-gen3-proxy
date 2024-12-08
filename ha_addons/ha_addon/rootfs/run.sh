#!/usr/bin/with-contenv bashio

echo "Add-on environment started"

echo "check for Home Assistant MQTT"
MQTT_HOST=$(bashio::services mqtt "host")
MQTT_PORT=$(bashio::services mqtt "port")
MQTT_USER=$(bashio::services mqtt "username")
MQTT_PASSWORD=$(bashio::services mqtt "password")

# wenn host gefunden wurde, dann nachricht ausgeben
if [ -z "$MQTT_HOST" ]; then
    echo "MQTT not found"
else
    echo "MQTT found"
    export MQTT_HOST
    export MQTT_PORT
    export MQTT_USER
    export MQTT_PASSWORD
fi



cd /home || exit

# Erstelle Ordner für log und config
mkdir -p proxy/log
mkdir -p proxy/config

cd /home/proxy || exit

export VERSION=$(cat /proxy-version.txt)

echo "Start Proxyserver..."
python3 server.py --json_config=/data/options.json
