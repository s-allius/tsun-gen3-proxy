#!/usr/bin/with-contenv bashio

bashio::log.blue "-----------------------------------------------------------"
bashio::log.blue "run.sh: info: setup Add-on environment"
bashio::cache.flush_all
MQTT_HOST=""
SLUG=""
HOSTNAME=""
if bashio::supervisor.ping; then
    bashio::log "run.sh: info: check Home Assistant bashio for config values"
    if bashio::services.available mqtt; then
        MQTT_HOST=$(bashio::services mqtt "host")
        MQTT_PORT=$(bashio::services mqtt "port")
        MQTT_USER=$(bashio::services mqtt "username")
        MQTT_PASSWORD=$(bashio::services mqtt "password")
    else
        bashio::log.yellow "run.sh: info: Home Assistant MQTT service not available!"
    fi
    SLUG=$(bashio::addon.repository)
    HOSTNAME=$(bashio::addon.hostname)
else
    bashio::log.red "run.sh: error: Home Assistant Supervisor API not available!"
fi

if [ -z "$SLUG" ]; then
    bashio::log.yellow "run.sh: info: addon slug not found"
else
    bashio::log.green "run.sh: info: found addon slug: $SLUG"
    export SLUG

fi
if [ -z "$HOSTNAME" ]; then
    bashio::log.yellow "run.sh: info: addon hostname not found"
else
    bashio::log.green "run.sh: info: found addon hostname: $HOSTNAME"
    export HOSTNAME
fi

# if a MQTT was/not found, drop a note
if [ -z "$MQTT_HOST" ]; then
    bashio::log.yellow "run.sh: info: MQTT config not found"
else
    bashio::log.green "run.sh: info: found MQTT config"
    export MQTT_HOST
    export MQTT_PORT
    export MQTT_USER
    export MQTT_PASSWORD
fi

# get logging config paramters
LOG_RETENTION=$(bashio::config "logging.retention_days" 2)
bashio::log.green "run.sh: info: addon log retention: $LOG_RETENTION days"

# overwrite log_lvl if available
LOG_LVL=$(bashio::config "logging.level" $LOG_LVL)
bashio::log.green "run.sh: info: addon log level: $LOG_LVL"


# Create folder for log und config files
mkdir -p /homeassistant/tsun-proxy/logs

cd /home/proxy || exit

export VERSION=$(cat /proxy-version.txt)
export SERVICE_NAME='TSUN-Proxy'

bashio::log.blue "run.sh: info: Start Proxyserver..."
bashio::log.blue "-----------------------------------------------------------"
/usr/bin/python3 /home/proxy/server.py --rel_urls --json_config=/data/options.json  --log_path=/homeassistant/tsun-proxy/logs/ --config_path=/homeassistant/tsun-proxy/ --log_backups=$LOG_RETENTION
