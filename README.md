<h1 align="center">TSUN-Gen3-Proxy</h1>
<p align="center">A proxy for</p>
<h3 align="center">TSUN Gen 3 Micro-Inverters</h3>
<p align="center">for easy</p>
<h3 align="center">MQTT/Home-Assistant</h3>
<p align="center">integration</p>
<p align="center">
    <a href="https://opensource.org/licenses/BSD-3-Clause"><img alt="License: BSD-3-Clause" src="https://img.shields.io/badge/License-BSD_3--Clause-green.svg"></a>
    <a href="https://www.python.org/downloads/release/python-3120/"><img alt="Supported Python versions" src="https://img.shields.io/badge/python-3.12-blue.svg"></a>
    <a href="https://sbtinstruments.github.io/aiomqtt/introduction.html"><img alt="Supported aiomqtt versions" src="https://img.shields.io/badge/aiomqtt-1.2.1-lightblue.svg"></a>
    <a href="https://toml.io/en/v1.0.0"><img alt="Supported toml versions" src="https://img.shields.io/badge/toml-1.0.0-lightblue.svg"></a>

</p>


###
# Overview

This proxy enables a reliable connection between TSUN third generation inverters and an MQTT broker. With the proxy, you can easily retrieve real-time values such as power, current and daily energy and integrate the inverter into typical home automations. This works even without an internet connection. The optional connection to the TSUN Cloud can be disabled!

In detail, the inverter establishes a TCP connection to the TSUN cloud to transmit current measured values every 300 seconds. To be able to forward the measurement data to an MQTT broker, the proxy must be looped into this TCP connection.

Through this, the inverter then establishes a connection to the proxy and the proxy establishes another connection to the TSUN Cloud. The transmitted data is interpreted by the proxy and then passed on to both the TSUN Cloud and the MQTT broker. The connection to the TSUN Cloud is optional and can be switched off in the configuration (default is on). Then no more data is sent to the Internet, but no more remote updates of firmware and operating parameters (e.g. rated power, grid parameters) are possible.

By means of `docker` a simple installation and operation is possible. By using `docker-composer`, a complete stack of proxy, `MQTT-brocker` and `home-assistant` can be started easily.
###
ℹ️ This project is not related to the company TSUN. It is a private initiative that aims to connect TSUN inverters with an MQTT broker. There is no support and no warranty from TSUN.
###

```
❗An essential requirement is that the proxy can be looped into the connection
between the inverter and TSUN Cloud.

There are various ways to do this, for example via an DNS host entry or via firewall
rules (iptables) in your router. However, depending on the circumstances, not all
of them are possible.

If you use a Pi-hole, you can also store the host entry in the Pi-hole.
```

## Features

- supports TSOL MS300, MS350, MS400, MS600, MS700 and MS800 inverters from TSUN
- `MQTT` support
- `Home-Assistant` auto-discovery support
- Self-sufficient island operation without internet
- non-root Docker Container

## Home Assistant Screenshots

Here are some screenshots of how the inverter is displayed in the Home Assistant:

https://github.com/s-allius/tsun-gen3-proxy/wiki/home-assistant#home-assistant-screenshots
## Requirements

- A running Docker engine to host the container
- Ability to loop the proxy into the connection between the inverter and the TSUN cloud


###
# Getting Started

To run the proxy, you first need to create the image. You can do this quite simply as follows:
```sh
docker build https://github.com/s-allius/tsun-gen3-proxy.git#main:app -t tsun-proxy
```
after that you can run the image:
```sh
docker run  --dns '8.8.8.8' --env 'UID=1000' -p '5005:5005'  -v ./config:/home/tsun-proxy/config -v ./log:/home/tsun-proxy/log tsun-proxy
```
You will surely see a message that the configuration file was not found. So that we can create this without admin rights, the `uid` must still be adapted. To do this, simply stop the proxy with ctrl-c and use the `id` command to determine your own UserId: 
```sh
% id 
uid=1050(sallius) gid=20(staff) ...
```
With this information we can customize the `docker run`` statement:
```sh
docker run  --dns '8.8.8.8' --env 'UID=1050' -p '5005:5005'  -v ./config:/home/tsun-proxy/config -v ./log:/home/tsun-proxy/log tsun-proxy
```

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
ha.proxy_node_id    = 'proxy'               # MQTT node id, for the proxy_node_id
ha.proxy_unique_id  = 'P170000000000001'    # MQTT unique id, to identify a proxy instance


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

## DNS Settings

### Loop the proxy into the connection
To include the proxy in the connection between the inverter and the TSUN Cloud, you must adapt the DNS record of *logger.talent-monitoring.com* within the network that your inverter uses. You need a mapping from logger.talent-monitoring.com to the IP address of the host running the Docker engine.

This can be done, for example, by adding a local DNS record to the Pi-hole if you are using it.

### DNS Rebind Protection
If you are using a router as local DNS server, the router may have DNS rebind protection that needs to be adjusted. For security reasons, DNS rebind protection blocks DNS queries that refer to an IP address on the local network.

If you are using a FRITZ!Box, you can do this in the Network Settings tab under Home Network / Network. Add logger.talent-monitoring.com as a hostname exception in DNS rebind protection.

### DNS server of proxy
The proxy itself must use a different DNS server to connect to the TSUN Cloud. If you use the DNS server with the adapted record, you will end up in an endless loop as soon as the proxy tries to send data to the TSUN Cloud.

As described above, set a DNS sever in the Docker command or Docker compose file.

## License

This project is licensed under the [BSD 3-clause License](https://opensource.org/licenses/BSD-3-Clause).

Note the aiomqtt library used is based on the paho-mqtt library, which has a dual license. One of the licenses is the so-called [Eclipse Distribution License v1.0](https://www.eclipse.org/org/documents/edl-v10.php). It is almost word-for-word identical to the BSD 3-clause License. The only differences are:

- One use of "COPYRIGHT OWNER" (EDL) instead of "COPYRIGHT HOLDER" (BSD)
- One use of "Eclipse Foundation, Inc." (EDL) instead of "copyright holder" (BSD)


## Versioning

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html). Breaking changes will only occur in major `X.0.0` releases.

## Contributing

We're very happy to receive contributions to this project! You can get started by reading [CONTRIBUTING.md](https://github.com/s-allius/tsun-gen3-proxy/blob/main/CONTRIBUTING.md).

## Changelog

The changelog lives in [CHANGELOG.md](https://github.com/s-allius/tsun-gen3-proxy/blob/main/CHANGELOG.md). It follows the principles of [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

