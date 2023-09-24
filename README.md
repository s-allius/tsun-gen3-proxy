<h1 align="center">TSUN-Gen3-Proxy</h1>
<p align="center">A proxy for</p>
<h3 align="center">TSUN Gen 3 Micro-Inverters</h3>
<p align="center">for easy</p>
<h3 align="center">MQTT/Home-Assistant</h3>
<p align="center">integration</p>
<p align="center">
    <a href="https://opensource.org/licenses/BSD-3-Clause"><img alt="License: BSD-3-Clause" src="https://img.shields.io/badge/License-BSD_3--Clause-green.svg"></a>
    <a href="https://www.python.org/downloads/release/python-3110/"><img alt="Supported Python versions" src="https://img.shields.io/badge/python-3.11-blue.svg"></a>
    <a href="https://sbtinstruments.github.io/aiomqtt/introduction.html"><img alt="Supported Python versions" src="https://img.shields.io/badge/aiomqtt-1.2.0-lightblue.svg"></a>
    <a href="https://toml.io/en/v1.0.0"><img alt="Supported Python versions" src="https://img.shields.io/badge/toml-1.0.0-lightblue.svg"></a>

</p>


###
# Overview

The "TSUN Gen3 Micro-Inverter" proxy enables a reliable connection between TSUN third generation inverters and an MQTT broker to integrate the inverter into typical home automations.

The inverter establishes a TCP connection to the TSUN Cloud to transmit current measured values every 300 seconds. To be able to forward the measurement data to an MQTT broker, the proxy must be looped into this TCP connection.

Through this, the inverter then establishes a connection to the proxy and the proxy establishes another connection to the TSUN Cloud. The transmitted data is interpreted by the proxy and then passed on to both the TSUN Cloud and the MQTT broker. The connection to the TSUN Cloud is optional and can be switched off in the configuration (default is on). Then no more data is sent to the Internet, but no more remote updates of firmware and operating parameters (e.g. rated power, grid parameters) are possible.

By means of `docker` a simple installation and operation is possible. By using `docker-composer`, a complete stack of proxy, `MQTT-brocker` and `home-assistant` can be started easily. 

```
❗An essential requirement is that the proxy can be looped into the connection between the inverter and TSUN Cloud.

There are various ways to do this, for example via DNS host entry or via firewall rules (iptables) in your router. However, depending on the circumstances, not all of them are possible.

If you use a PiHole, you can also store the host entry in the PiHole.
```

## Features

- `MQTT` support
- `Home-Assistant` auto-discovery support
- Self-sufficient island operation without internet
- non-root Docker Container

## Requirements

- A running Docker engine to host the container
- Ability to loop the proxy into the connection between the inverter and the TSUN cloud

## License

This project is licensed under the [BSD 3-clause License](https://opensource.org/licenses/BSD-3-Clause).

Note the used aiomqtt library whichthat the underlying paho-mqtt library is dual-licensed. One of the licenses is the so-called [Eclipse Distribution License v1.0](https://www.eclipse.org/org/documents/edl-v10.php). It is almost word-for-word identical to the BSD 3-clause License. The only differences are:

- One use of "COPYRIGHT OWNER" (EDL) instead of "COPYRIGHT HOLDER" (BSD)
- One use of "Eclipse Foundation, Inc." (EDL) instead of "copyright holder" (BSD)


## Versioning

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html). Breaking changes will only occur in major `X.0.0` releases.

## Changelog

The changelog lives in [CHANGELOG.md](https://github.com/s-allius/tsun-gen3-proxy/blob/main/CHANGELOG.md). It follows the principles of [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

###
# Configuration
The Docker container does not require any special configuration. 
On the host, two directories (for log files and for config files) must be mapped. If necessary, the UID of the proxy process can be adjusted, which is also the owner of the log and configuration files.

The proxy can be configured via the file 'config.toml'. When the proxy is started, a file 'config.example.toml' is copied into the config directory. This file shows all possible parameters and their default values. Changes in the example file itself are not evaluated. To configure the proxy, the config.example.toml file should be renamed to config.toml. After that the corresponding values can be adjusted. To load the new configuration, the proxy must be restarted. 


## Proxy Configuration
The configration uses the TOML format, which aims to be easy to read due to obvious semantics.
You find more details here: https://toml.io/en/v1.0.0



```toml
# configuration to reach tsun cloud
tsun.enabled = true   # false: disables connecting to the tsun cloud, and avoids updates
tsun.host    = 'logger.talent-monitoring.com'
tsun.port    = 5005


# mqtt broker configuration
mqtt.host    = 'mqtt'   # URL or IP address of the mqtt broker
mqtt.port    = 1883
mqtt.user    = ''
mqtt.passwd  = ''


# home-assistant
ha.auto_conf_prefix = 'homeassistant'       # MQTT prefix for subscribing for homeassistant status updates
ha.discovery_prefix = 'homeassistant'       # MQTT prefix for discovery topic 
ha.entity_prefix    = 'tsun'                # MQTT topic prefix for publishing inverter values


# microinverters
inverters.allow_all = false   # True: allow inverters, even if we have no inverter mapping

# inverter mapping, maps a `serial_no* to a `node_id` and defines an optional `suggested_area` for `home-assistant`
#
# for each inverter add a block starting with [inverters."<16-digit serial numbeer>"]
[inverters."R17xxxxxxxxxxxx1"]
node_id = 'inv1'              # Optional, MQTT replacement for inverters serial number  
suggested_area = 'roof'       # Optional, suggested installation area for home-assistant

[inverters."R17xxxxxxxxxxxx2"]
node_id = 'inv2'              # Optional, MQTT replacement for inverters serial number  
suggested_area = 'balcony'    # Optional, suggested installation area for home-assistant


```

