# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

- refactoring of the connection classes
- change user id on startup
- register MQTT topics to home assistant, even if we have multiple inverters

## [0.0.6] - 2023-10-03

- Bump aiomqtt to version 1.2.1
- Force MQTT registration when the home assistant has set the status to online again
- fix control byte output in tx trace
- dealloc async_stream instances in connection termination

## [0.0.5] - 2023-10-01

- Entity icons updated
- Prints version on start
- Prepare for MQTT component != sensor
- Add MQTT origin
  
## [0.0.4] - 2023-09-30

- With this patch we ignore the setting 'suggested_area' in config.toml, because it makes no sense with multiple devices. We are looking for a better solution without combining all values into one area again in a later version.
  
❗Due to the change from one device to multiple devices in the Home Assistant, the previous MQTT device should be deleted in the Home Assistant after the update to pre-release '0.0.4'. Afterwards, the proxy must be restarted again to ensure that the sub-devices are created completely.

### Added

- Register multiple devices at home-assistant instead of one for all measurements.
  Now we register: a Controller, the inverter and up to 4 input devices to home-assistant.
  
## [0.0.3] - 2023-09-28

### Added

- Fixes Running Proxy with host UID and GUID #2

## [0.0.2] - 2023-09-27

### Added

- Dockerfile opencontainer labels
- Send voltage and current of inputs to mqtt

## [0.0.1] - 2023-09-25

### Added

- Logger for inverter packets
- SIGTERM handler for fast docker restarts
- Proxy as non-root docker application 
- Unit- and system tests
- Home asssistant auto configuration
- Self-sufficient island operation without internet

## [0.0.0] - 2023-08-21

### Added

- First checkin, the project was born