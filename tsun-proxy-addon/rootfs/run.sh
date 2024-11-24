#!/usr/bin/with-contenv bashio

echo "Add-on environment started"


cd /home/tsun-proxy/src || exit


echo "Erstelle config.toml"
python3 create_config_toml.py



echo "Starte Webserver"
python3 server.py
