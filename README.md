<h1 align="center">TSUN-Gen3-Proxy</h1>
<p align="center">A proxy for</p>
<h3 align="center">TSUN Gen 3 Micro-Inverters</h3>
<p align="center">for easy</p>
<h3 align="center">MQTT/Home-Assistant</h3>
<p align="center">integration</p>
<p align="center">
    <a href="https://opensource.org/licenses/BSD-3-Clause"><img alt="License: BSD-3-Clause" src="https://img.shields.io/badge/License-BSD_3--Clause-green.svg"></a>
    <a href="https://www.python.org/downloads/release/python-3120/"><img alt="Supported Python versions" src="https://img.shields.io/badge/python-3.12-blue.svg"></a>
    <a href="https://sbtinstruments.github.io/aiomqtt/introduction.html"><img alt="Supported aiomqtt versions" src="https://img.shields.io/badge/aiomqtt-2.3.0-lightblue.svg"></a>
    <a href="https://libraries.io/pypi/aiocron"><img alt="Supported aiocron versions" src="https://img.shields.io/badge/aiocron-1.8-lightblue.svg"></a>
    <a href="https://toml.io/en/v1.0.0"><img alt="Supported toml versions" src="https://img.shields.io/badge/toml-1.0.0-lightblue.svg"></a>
    <br>
    <a href="https://sonarcloud.io/component_measures?id=s-allius_tsun-gen3-proxy&metric=alert_status"><img alt="The quality gate status" src="https://sonarcloud.io/api/project_badges/measure?project=s-allius_tsun-gen3-proxy&metric=alert_status"></a>
    <a href="https://sonarcloud.io/component_measures?id=s-allius_tsun-gen3-proxy&metric=bugs"><img alt="No of bugs" src="https://sonarcloud.io/api/project_badges/measure?project=s-allius_tsun-gen3-proxy&metric=bugs"></a>
    <a href="https://sonarcloud.io/component_measures?id=s-allius_tsun-gen3-proxy&metric=code_smells"><img alt="No of code-smells" src="https://sonarcloud.io/api/project_badges/measure?project=s-allius_tsun-gen3-proxy&metric=code_smells"></a>
    <br>
    <a href="https://sonarcloud.io/component_measures?id=s-allius_tsun-gen3-proxy&metric=coverage"><img alt="Test coverage in percent" src="https://sonarcloud.io/api/project_badges/measure?project=s-allius_tsun-gen3-proxy&metric=coverage"></a>
</p>

# Overview

This proxy enables a reliable connection between TSUN third generation inverters and an MQTT broker. With the proxy, you can easily retrieve real-time values such as power, current and daily energy and integrate the inverter into typical home automations. This works even without an internet connection. The optional connection to the TSUN Cloud can be disabled!

In detail, the inverter establishes a TCP connection to the TSUN cloud to transmit current measured values every 300 seconds. To be able to forward the measurement data to an MQTT broker, the proxy must be looped into this TCP connection.

Through this, the inverter then establishes a connection to the proxy and the proxy establishes another connection to the TSUN Cloud. The transmitted data is interpreted by the proxy and then passed on to both the TSUN Cloud and the MQTT broker. The connection to the TSUN Cloud is optional and can be switched off in the configuration (default is on). Then no more data is sent to the Internet, but no more remote updates of firmware and operating parameters (e.g. rated power, grid parameters) are possible.

By means of `docker` a simple installation and operation is possible. By using `docker-composer`, a complete stack of proxy, `MQTT-brocker` and `home-assistant` can be started easily.

Alternatively you can run the TSUN-Proxy as a Home Assistant Add-on. The installation of this add-on is pretty straightforward and not different in comparison to installing any other custom Home Assistant add-on.
Follow the Instructions mentioned in the add-on subdirectory `ha_addons`.

<br>
ℹ️ This project is not related to the company TSUN. It is a private initiative that aims to connect TSUN inverters with an MQTT broker. There is no support and no warranty from TSUN.
<br><br>

```txt
❗An essential requirement is that the proxy can be looped into the connection
between the inverter and TSUN Cloud.

There are various ways to do this, for example via an DNS host entry or via firewall
rules (iptables) in your router. However, depending on the circumstances, not all
of them are possible.

If you use a Pi-hole, you can also store the host entry in the Pi-hole.
```

## Features

- Supports TSUN GEN3 PLUS inverters: TSOL-MS2000, MS1800 and MS1600
- Supports TSUN GEN3 inverters: TSOL-MS800, MS700, MS600, MS400, MS350 and MS300
- `MQTT` support
- `Home-Assistant` auto-discovery support
- `MODBUS` support via MQTT topics
- `AT-Command` support via MQTT topics (GEN3PLUS only)
- Faster DataUp interval sends measurement data to the MQTT broker every minute
- Self-sufficient island operation without internet
- Security-Features:
  - control access via `AT-commands`
  - Runs in a non-root Docker Container

## Home Assistant Screenshots

Here are some screenshots of how the inverter is displayed in the Home Assistant:

<https://github.com/s-allius/tsun-gen3-proxy/wiki/home-assistant#home-assistant-screenshots>

## Requirements

### for Docker Installation

- A running Docker engine to host the container
- Ability to loop the proxy into the connection between the inverter and the TSUN cloud

### for Home Assistant Add-on Installation

- Running Home Assistant on Home Assistant OS or Supervised. Container and Core installations doesn't support add-ons.
- Ability to loop the proxy into the connection between the inverter and the TSUN cloud

# Getting Started

## for Docker Installation

To run the proxy, you first need to create the image. You can do this quite simply as follows:

```sh
docker build https://github.com/s-allius/tsun-gen3-proxy.git#main:app -t tsun-proxy
```

after that you can run the image:

```sh
docker run  --dns '8.8.8.8' --env 'UID=1000' -p '5005:5005' -p '10000:10000' -v ./config:/home/tsun-proxy/config -v ./log:/home/tsun-proxy/log tsun-proxy
```

You will surely see a message that the configuration file was not found. So that we can create this without admin rights, the `uid` must still be adapted. To do this, simply stop the proxy with ctrl-c and use the `id` command to determine your own UserId:

```sh
% id 
uid=1050(sallius) gid=20(staff) ...
```

With this information we can customize the `docker run`` statement:

```sh
docker run  --dns '8.8.8.8' --env 'UID=1050' -p '5005:5005' -p '10000:10000' -v ./config:/home/tsun-proxy/config -v ./log:/home/tsun-proxy/log tsun-proxy
```

## for Home Assistant Add-on Installation

1. Add the repository URL to the Home Assistant add-on store
[![Add repository on my Home Assistant][repository-badge]][repository-url]
2. Reload the add-on store page
3. Click the "Install" button to install the add-on.

# Configuration

```txt
❗The following describtion applies to docker installation. For Home Assistant Add-on installation, the 
configuration is done via the Home Assistant UI. Some options are not required, nor is the e creation of a 
config.toml file.. For general understandment of the configuration, you can read the following describtion.
```

The configuration consists of several parts. First, the container and the proxy itself must be configured, and then the connection of the inverter to the proxy must be set up, which is done differently depending on the inverter generation

For GEN3PLUS inverters, this can be done easily via the web interface of the inverter. The GEN3 inverters do not have a web interface, so the proxy is integrated via a modified DNS resolution.

  1. [Container Setup](#container-setup)
  2. [Proxy Configuration](#proxy-configuration)
  3. [Inverter Configuration](#inverter-configuration) (only GEN3PLUS)
  4. [DNS Settings](#dns-settings) (Mandatory for GEN3)

## Container Setup

No special configuration is required for the Docker container if it is built and started as described above. It is recommended to start the container with docker-compose. The configuration is then specified in a docker-compose.yaml file. An example of a stack consisting of the proxy, MQTT broker and home assistant can be found [here](https://github.com/s-allius/tsun-gen3-proxy/blob/main/docker-compose.yaml).

On the host, two directories (for log files and for config files) must be mapped. If necessary, the UID of the proxy process can be adjusted, which is also the owner of the log and configuration files.

A description of the configuration parameters can be found [here](https://github.com/s-allius/tsun-gen3-proxy/wiki/Configuration-details#docker-compose-environment-variables).

## Proxy Configuration

The proxy can be configured via the file 'config.toml'. When the proxy is started, a file 'config.example.toml' is copied into the config directory. This file shows all possible parameters and their default values. Changes in the example file itself are not evaluated. To configure the proxy, the config.example.toml file should be renamed to config.toml. After that the corresponding values can be adjusted. To load the new configuration, the proxy must be restarted.

The configration uses the TOML format, which aims to be easy to read due to obvious semantics.
You find more details here: <https://toml.io/en/v1.0.0>

<details>
<summary>Here is an example of a <b>config.toml</b> file</summary>

```toml
##########################################################################################
###
###          T S U N  -  G E N 3  -   P R O X Y
### 
###                from   Stefan Allius
###
##########################################################################################
###
###   The readme will give you an overview of the project:
###   https://s-allius.github.io/tsun-gen3-proxy/
###
###   The proxy supports different operation modes. Select the proper mode 
###   which depends on your inverter type and you inverter firmware. 
###   Please read: 
###   https://github.com/s-allius/tsun-gen3-proxy/wiki/Operation-Modes-Overview
###
###   Here you will find a description of all configuration options:
###   https://github.com/s-allius/tsun-gen3-proxy/wiki/Configuration-details
###
###   The configration uses the TOML format, which aims to be easy to read due to 
###   obvious semantics. You find more details here: https://toml.io/en/v1.0.0
###
##########################################################################################


##########################################################################################
##
## MQTT broker configuration
##
## In this block, you must configure the connection to your MQTT broker and specify the
## required credentials. As the proxy does not currently support an encrypted connection
## to the MQTT broker, it is strongly recommended that you do not use a public broker.
##
## https://github.com/s-allius/tsun-gen3-proxy/wiki/Configuration-details#mqtt-broker-account
##

mqtt.host    = 'mqtt'   # URL or IP address of the mqtt broker
mqtt.port    = 1883
mqtt.user    = ''
mqtt.passwd  = ''


##########################################################################################
##
## HOME ASSISTANT
##
## The proxy supports the MQTT autoconfiguration of Home Assistant (HA). The default 
## values match the HA default configuration. If you need to change these or want to use
## a different MQTT client, you can adjust the prefixes of the MQTT topics below.
##
## https://github.com/s-allius/tsun-gen3-proxy/wiki/Configuration-details#home-assistant
##

ha.auto_conf_prefix = 'homeassistant'       # MQTT prefix for subscribing for homeassistant status updates
ha.discovery_prefix = 'homeassistant'       # MQTT prefix for discovery topic 
ha.entity_prefix    = 'tsun'                # MQTT topic prefix for publishing inverter values
ha.proxy_node_id    = 'proxy'               # MQTT node id, for the proxy_node_id
ha.proxy_unique_id  = 'P170000000000001'    # MQTT unique id, to identify a proxy instance


##########################################################################################
##
## GEN3 Proxy Mode Configuration
##
## In this block, you can configure an optional connection to the TSUN cloud for GEN3
## inverters. This connection is only required if you want send data to the TSUN cloud
## to use the TSUN APPs or receive firmware updates.  
##
## https://github.com/s-allius/tsun-gen3-proxy/wiki/Configuration-details#tsun-cloud-for-gen3-inverter-only
##

tsun.enabled = true   # false: disables connecting to the tsun cloud, and avoids updates
tsun.host    = 'logger.talent-monitoring.com'
tsun.port    = 5005


##########################################################################################
##
## GEN3PLUS Proxy Mode Configuration
##
## In this block, you can configure an optional connection to the TSUN cloud for GEN3PLUS
## inverters. This connection is only required if you want send data to the TSUN cloud
## to use the TSUN APPs or receive firmware updates.  
##
## https://github.com/s-allius/tsun-gen3-proxy/wiki/Configuration-details#solarman-cloud-for-gen3plus-inverter-only
##
solarman.enabled = true   # false: disables connecting to the tsun cloud, and avoids updates
solarman.host    = 'iot.talent-monitoring.com'
solarman.port    = 10000


##########################################################################################
###
### Inverter Definitions
###
### The proxy supports the simultaneous operation of several inverters, even of different
### types. A configuration block must be defined for each inverter, in which all necessary
### parameters must be specified. These depend on the operation mode used and also differ
### slightly depending on the inverter type.
###
### In addition, the PV modules can be defined at the individual inputs for documentation
### purposes, whereby these are displayed in Home Assistant.
###
### The proxy only accepts connections from known inverters. This can be switched off for
### test purposes and unknown serial numbers are also accepted. 
###

inverters.allow_all = false   # only allow known inverters


##########################################################################################
##
## For each GEN3 inverter, the serial number of the inverter must be mapped to an MQTT
## definition. To do this, the corresponding configuration block is started with
## `[Inverter.“<16-digit serial number>”]` so that all subsequent parameters are assigned
## to this inverter. Further inverter-specific parameters (e.g. polling mode) can be set
## in the configuration block
##
## The serial numbers of all GEN3 inverters start with `R17`!
##

[inverters."R17xxxxxxxxxxxx1"]
node_id = 'inv_1'            # MQTT replacement for inverters serial number  
suggested_area = 'roof'      # suggested installation place for home-assistant
modbus_polling = false       # Disable optional MODBUS polling for GEN3 inverter
pv1 = {type = 'RSM40-8-395M', manufacturer = 'Risen'}   # Optional, PV module descr
pv2 = {type = 'RSM40-8-395M', manufacturer = 'Risen'}   # Optional, PV module descr


##########################################################################################
##
## For each GEN3PLUS inverter, the serial number of the inverter must be mapped to an MQTT
## definition. To do this, the corresponding configuration block is started with
## `[Inverter.“<16-digit serial number>”]` so that all subsequent parameters are assigned
## to this inverter. Further inverter-specific parameters (e.g. polling mode, client mode)
## can be set in the configuration block
## 
## The serial numbers of all GEN3PLUS inverters start with `Y17` or Y47! Each GEN3PLUS
## inverter is supplied with a “Monitoring SN:”. This can be found on a sticker enclosed
## with the inverter.
##

[inverters."Y17xxxxxxxxxxxx1"]  # This block is also for inverters with a Y47 serial no
monitor_sn = 2000000000      # The GEN3PLUS "Monitoring SN:"
node_id = 'inv_2'            # MQTT replacement for inverters serial number  
suggested_area = 'garage'    # suggested installation place for home-assistant
modbus_polling = true        # Enable optional MODBUS polling

# if your inverter supports SSL connections you must use the client_mode. Pls, uncomment
# the next line and configure the fixed IP of your inverter
#client_mode = {host = '192.168.0.1', port = 8899}       

pv1 = {type = 'RSM40-8-410M', manufacturer = 'Risen'}   # Optional, PV module descr
pv2 = {type = 'RSM40-8-410M', manufacturer = 'Risen'}   # Optional, PV module descr
pv3 = {type = 'RSM40-8-410M', manufacturer = 'Risen'}   # Optional, PV module descr
pv4 = {type = 'RSM40-8-410M', manufacturer = 'Risen'}   # Optional, PV module descr


##########################################################################################
###
### If the proxy mode is configured, commands from TSUN can be sent to the inverter via
### this connection or parameters (e.g. network credentials) can be queried. Filters can
### then be configured for the AT+ commands from the TSUN Cloud so that only certain
### accesses are permitted.
###
### An overview of all known AT+ commands can be found here:
### https://github.com/s-allius/tsun-gen3-proxy/wiki/AT--commands
###

[gen3plus.at_acl]
tsun.allow = ['AT+Z', 'AT+UPURL', 'AT+SUPDATE']   # allow this for TSUN access
tsun.block = []                                   
mqtt.allow = ['AT+']                              # allow all via mqtt
mqtt.block = []

```

</details>

## Inverter Configuration

GEN3PLUS inverters offer a web interface that can be used to configure the inverter. This is very practical for sending the data directly to the proxy. On the one hand, the inverter broadcasts its own SSID on 2.4GHz. This can be recognized because it is broadcast with `AP_<Montoring SN>`. You will find the `Monitor SN` and the password for the WLAN connection on a small sticker enclosed with the inverter.

If you have already connected the inverter to the cloud via the TSUN app, you can also address the inverter directly via WiFi. In the first case, the inverter uses the fixed IP address `10.10.100.254`, in the second case you have to look up the IP address in your router.

The standard web interface of the inverter can be accessed at `http://<ip-adress>/index_cn.html`. Here you can set up the WLAN connection or change the password. The default user and password is `admin`/`admin`.

For our purpose, the hidden URL `http://<ip-adress>/config_hide.html` should be called. There you can see and modify the parameters for accessing the cloud. Here we enter the IP address of our proxy and the IP port `10000` for the `Server A Setting` and for `Optional Server Setting`. The second entry is used as a backup in the event of connection problems.

```txt
❗If the IP port is set to 10443 in the inverter configuration, you probably have a firmware with SSL support.
In this case, you MUST NOT change the port or the host address, as this may cause the inverter to hang and
require a complete reset. Use the configuration in client mode instead.
```

If access to the web interface does not work, it can also be redirected via DNS redirection, as is necessary for the GEN3 inverters.

## Client Mode (GEN3PLUS only)

Newer GEN3PLUS inverters support SSL encrypted connections over port 10443 to the TSUN cloud. In this case you can't loop the proxy into this connection, since the certicate verification of the inverter don't allow this. You can configure the proxy in client-mode to establish an unencrypted connection to the inverter. For this porpuse the inverter listen on port `8899`.

There are some requirements to be met:

- the inverter should have a fixed IP
- the proxy must be able to reach the inverter. You must configure a corresponding route in your router if the inverter and the proxy are in different IP networks
- add a 'client_mode' line to your config.toml file, to specify the inverter's ip address

## DNS Settings

### Loop the proxy into the connection

To include the proxy in the connection between the inverter and the TSUN Cloud, you must adapt the DNS record of *logger.talent-monitoring.com* within the network that your inverter uses. You need a mapping from logger.talent-monitoring.com to the IP address of the host running the Docker engine.

The new GEN3 PLUS inverters use a different URL. Here, *iot.talent-monitoring.com* must be redirected.

This can be done, for example, by adding a local DNS record to the Pi-hole if you are using it.

### DNS Rebind Protection

If you are using a router as local DNS server, the router may have DNS rebind protection that needs to be adjusted. For security reasons, DNS rebind protection blocks DNS queries that refer to an IP address on the local network.

If you are using a FRITZ!Box, you can do this in the Network Settings tab under Home Network / Network. Add logger.talent-monitoring.com as a hostname exception in DNS rebind protection.

### DNS server of proxy

The proxy itself must use a different DNS server to connect to the TSUN Cloud. If you use the DNS server with the adapted record, you will end up in an endless loop as soon as the proxy tries to send data to the TSUN Cloud.

As described above, set a DNS sever in the Docker command or Docker compose file.

### Over The Air (OTA) firmware update

Even if the proxy is connected between the inverter and the TSUN Cloud, an OTA update is supported. To do this, the inverter must be able to reach the website <http://www.talent-monitoring.com:9002/> in order to download images from there.

It must be ensured that this address is not mapped to the proxy!

# General Information

## Compatibility

In the following table you will find an overview of which inverter model has been tested for compatibility with which firmware version.
A combination with a red question mark should work, but I have not checked it in detail.

<table align="center">
  <tr><th align="center">Micro Inverter Model</th><th align="center">Fw. 1.00.06</th><th align="center">Fw. 1.00.17</th><th align="center">Fw. 1.00.20</th><th align="center">Fw. 4.0.10</th><th align="center">Fw. 4.0.20</th></tr>
  <tr><td>GEN3 micro inverters (single MPPT):<br>MS300, MS350, MS400<br>MS400-D</td><td align="center">❓</td><td align="center">❓</td><td align="center">❓</td><td align="center">➖</td><td align="center">➖</td></tr>
  <tr><td>GEN3 micro inverters (dual MPPT):<br>MS600, MS700, MS800<br>MS600-D, MS800-D</td><td align="center">✔️</td><td align="center">✔️</td><td align="center">✔️</td><td align="center">➖</td><td align="center">➖</td></tr>
  <tr><td>GEN3 PLUS micro inverters:<br>MS1600, MS1800, MS2000<br>MS2000-D</td><td align="center">➖</td><td align="center">➖</td><td align="center">➖</td><td align="center">✔️</td><td align="center">✔️</td></tr>
  <tr><td>TITAN micro inverters:<br>TSOL-MP3000, MP2250, MS3000</td><td align="center">❓</td><td align="center">❓</td><td align="center">❓</td><td align="center">❓</td><td align="center">❓</td></tr>
</table>

```txt
Legend
➖: Firmware not available for this devices
✔️: proxy support testet
❓: proxy support possible but not testet
🚧: Proxy support in preparation
```

❗The new inverters of the GEN3 Plus generation (e.g. MS-2000) use a completely different protocol for data transmission to the TSUN server. These inverters are supported from proxy version 0.6. The serial numbers of these inverters start with `Y17E` or `Y47E` instead of `R17E`

If you have one of these combinations with a red question mark, it would be very nice if you could send me a proxy trace so that I can carry out the detailed checks and adjust the device and system tests. [Ask here how to send a trace](https://github.com/s-allius/tsun-gen3-proxy/discussions/categories/traces-for-compatibility-check)

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

[repository-badge]: https://img.shields.io/badge/Add%20repository%20to%20my-Home%20Assistant-41BDF5?logo=home-assistant&style=for-the-badge
[repository-url]: https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fs-allius%2Ftsun-gen3-proxy
