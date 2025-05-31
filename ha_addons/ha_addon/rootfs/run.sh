#!/usr/bin/with-contenv bashio

echo "run.sh: info: Add-on environment started"
bashio::cache.flush_all
echo "run.sh: info: check for Home Assistant supervisor API"
MQTT_HOST=""
if bashio::supervisor.ping; then
    echo "run.sh: info: check for Home Assistant MQTT"
    if bashio::services mqtt; then
        MQTT_HOST=$(bashio::services mqtt "host")
        MQTT_PORT=$(bashio::services mqtt "port")
        MQTT_USER=$(bashio::services mqtt "username")
        MQTT_PASSWORD=$(bashio::services mqtt "password")
    else
        echo "run.sh: error: Home Assistant service MQTT not available!"
    fi
else
    echo "run.sh: error: Home Assistant supervisor API not available!"
fi

# if a MQTT was/not found, drop a note
if [ -z "$MQTT_HOST" ]; then
    echo "run.sh: info: MQTT configuration not found"
else
    echo "run.sh: info: MQTT found"
    export MQTT_HOST
    export MQTT_PORT
    export MQTT_USER
    export MQTT_PASSWORD
fi




# Create folder for log und config files
mkdir -p /homeassistant/tsun-proxy/logs

cd /home/proxy || exit

export VERSION=$(cat /proxy-version.txt)

echo "Start Proxyserver..."
python3 server.py --rel_urls --json_config=/data/options.json  --log_path=/homeassistant/tsun-proxy/logs/ --config_path=/homeassistant/tsun-proxy/ --log_backups=2
