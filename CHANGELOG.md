# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

- Fixed detection of the connected inputs/MPPTs
- Add data acquisition interval
- Add number of connections
- Add communication type
- Preparation for overwriting received data

## [0.5.4] - 2023-11-22

- hardening remove dangerous commands from busybox
- add OTA start message counter
- add message handler for over the air updates
- add unit tests for ota messages
- add unit test for int64 data type
- cleanup msg_get_time_handler
- remove python packages setuptools, wheel, pip from final image to reduce the attack surface

## [0.5.3] - 2023-11-12

- remove apk packet manager from the final image
- send contact info every time a client connection is established
- use TSUN timestamp instead of local time, as TSUN also expects Central European Summer Time in winter

## [0.5.2] - 2023-11-09

- add int64 data type to info parser
- allow multiple calls to Message.close()
- check for race cond. on closing and establishing client connections

## [0.5.1] - 2023-11-05

- fixes f-string by limes007
- add description for dns settings by limes007

## [0.5.0] - 2023-11-04

- fix issue [#21](https://github.com/s-allius/tsun-gen3-proxy/issues/21)
- register proxy dev as soon as the MQTT connection is established
- increase test coverage of the Messages class
- add error counter for unknown control bytes
- lint code with flake8
  
## [0.4.3] - 2023-10-26

- fix typos by Lenz Grimmer
- catch mqtt errors, so we can forward messages to tsun even if the mqtt broker is not reachable
- avoid resetting the daily generation counters even if the inverter sends zero values after reconnection

## [0.4.2] - 2023-10-21

- count unknown data types in received messages
- count definition errors in our internal tables
- increase test coverage of the Infos class to 100%
- avoid resetting the daily generation counters even if the inverter sends zero values at sunset

## [0.4.1] - 2023-10-20

- fix issue [#18](https://github.com/s-allius/tsun-gen3-proxy/issues/18)
- initialize the proxy statistics
- avoid resetting total generation counters
  
## [0.4.0] - 2023-10-16

- fix issue [#8](https://github.com/s-allius/tsun-gen3-proxy/issues/8)
- implement [#10](https://github.com/s-allius/tsun-gen3-proxy/issues/10)
- fix: don't dispatch ignored messages so that they are not forwarded
- add systemtests
- fix unit tests, which were broken since version 0.3.0
- add proxy device to home assistant
- add statistic counter to proxy device
- support multiple inverter registration at home assistant
  
## [0.3.0] - 2023-10-10

❗Due to the definition of values for diagnostics, the MQTT devices of controller and inverter should be deleted in the Home Assistant before updating to version '0.3.0'. After the update, these are automatically created again. The measurement data is retained.

### Changes

- optimize and reduce logging
- switch to pathon 3.12
- classify some values for diagnostics
  
## [0.2.0] - 2023-10-07

This version halves the size of the Docker image and reduces the attack surface for security vulnerabilities, by omitting unneeded code. The feature set is exactly the same as the previous release version 0.1.0.

### Changes in 0.2.0

- move from slim-bookworm to an alpine base image
- install python requirements with pip wheel
- disable DEBUG log for releases
- support building of release candidates

## [0.1.0] - 2023-10-06

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

### Added in 0.0.4

- Register multiple devices at home-assistant instead of one for all measurements.
  Now we register: a Controller, the inverter and up to 4 input devices to home-assistant.
  
## [0.0.3] - 2023-09-28

### Added in 0.0.3

- Fixes Running Proxy with host UID and GUID #2

## [0.0.2] - 2023-09-27

### Added in 0.0.2

- Dockerfile opencontainer labels
- Send voltage and current of inputs to mqtt

## [0.0.1] - 2023-09-25

### Added in 0.0.1

- Logger for inverter packets
- SIGTERM handler for fast docker restarts
- Proxy as non-root docker application
- Unit- and system tests
- Home asssistant auto configuration
- Self-sufficient island operation without internet

## [0.0.0] - 2023-08-21

### Added

- First checkin, the project was born
