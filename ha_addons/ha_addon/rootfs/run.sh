#!/usr/bin/with-contenv bashio

bashio::log.blue "-----------------------------------------------------------"
bashio::log.blue "run.sh: info: setup Add-on environment"
bashio::cache.flush_all
MQTT_HOST=""
if bashio::supervisor.ping; then
    bashio::log "run.sh: info: check for Home Assistant MQTT service"
    if bashio::services.available mqtt; then
        MQTT_HOST=$(bashio::services mqtt "host")
        MQTT_PORT=$(bashio::services mqtt "port")
        MQTT_USER=$(bashio::services mqtt "username")
        MQTT_PASSWORD=$(bashio::services mqtt "password")
    else
        bashio::log.yellow "run.sh: info: Home Assistant MQTT service not available!"
    fi
else
    bashio::log.red "run.sh: error: Home Assistant Supervisor API not available!"
fi

# if a MQTT was/not found, drop a note
if [ -z "$MQTT_HOST" ]; then
    bashio::log.yellow "run.sh: info: MQTT config not found"
else
    bashio::log.green "run.sh: info: MQTT config found"
    export MQTT_HOST
    export MQTT_PORT
    export MQTT_USER
    export MQTT_PASSWORD
fi




# Create folder for log und config files
mkdir -p /homeassistant/tsun-proxy/logs

cd /home/proxy || exit

export VERSION=$(cat /proxy-version.txt)

bashio::log.blue "run.sh: info: Start Proxyserver..."
bashio::log.blue "-----------------------------------------------------------"
python3 server.py --rel_urls --json_config=/data/options.json  --log_path=/homeassistant/tsun-proxy/logs/ --config_path=/homeassistant/tsun-proxy/ --log_backups=2
