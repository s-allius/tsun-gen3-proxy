# Home Assistant Add-on: TSUN Proxy

[TSUN Proxy][tsunproxy] enables a reliable connection between TSUN third generation
inverters and an MQTT broker. With the proxy, you can easily retrieve real-time values
such as power, current and daily energy and integrate the inverter into Home Assistant.
This works even without an internet connection.
The optional connection to the TSUN Cloud can be disabled!

## Pre-requisites

1. This Add-on requires an MQTT broker to work.
For a typical installation, we recommend the [Mosquitto add-on][Mosquitto] running on your Home Assistant.

2. You need to loop the proxy into the connection between the inverter and the TSUN Cloud,
you must adapt the DNS record within the network that your inverter uses. You need a mapping
from logger.talent-monitoring.com and/or iot.talent-monitoring.com to the IP address of your
Home Assistant.
This can be done, for example, by adding a local DNS record to [AdGuard Home Add-on][AdGuard]
(navigate to `filters` on the AdGuard panel and add an entry under `custom filtering rules`).

## Installation

The installation of this add-on is pretty straightforward and not different in
comparison to installing any other Home Assistant add-on.

1. Add the repository URL to the Home Assistant add-on store
[![Add repository on my Home Assistant][repository-badge]][repository-url]
2. Reload the add-on store page
3. Click the "Install" button to install the add-on.
4. Add your inverter configuration to the add-on configuration
5. Start the "TSUN-Proxy" add-on
6. Check the logs of the "TSUN-Proxy" add-on to see if everything went well.

_Please note, the add-on is pre-configured to connect with
Home Assistants default MQTT Broker. There is no need to configure any MQTT parameters
if you're running an MOSQUITTO add-on. Home Assistant communication and TSUN Cloud URL
and Ports are also pre-configured._

This automatic handling of the TSUN Cloud and MQTT Broker conflicts with the
[TSUN Proxy official documentation][tsunproxy]. The official documentation
will state `mqtt.host`, `mqtt.port`, `mqtt.user`, `mqtt.passwd` `solarman.host`,
`solarman.port` `tsun.host`, `tsun.port` and Home Assistant options are required.
For the add-on, however, this isn't needed.

## Configuration

**Note**: _Remember to restart the add-on when the configuration is changed._

Example add-on configuration after installation:

```yaml
inverters:
  - serial: R17E760702080400
    node_id: PV-Garage
    suggested_area: Garage
    modbus_polling: false
    pv1.manufacturer: Shinefar
    pv1.type: SF-M18/144550
    pv2.manufacturer: Shinefar
    pv2.type: SF-M18/144550
```

**Note**: _This is just an example, you need to replace the values with your own!_

Example add-on configuration for GEN3PLUS inverters:

```yaml
inverters:
  - serial: Y17000000000000
    monitor_sn: '2000000000'
    node_id: PV-Garage
    suggested_area: Garage
    modbus_polling: true
    client_mode.host: 192.168.x.x
    client_mode.port: 8899
    client_mode.forward: true
    pv1.manufacturer: Shinefar
    pv1.type: SF-M18/144550
    pv2.manufacturer: Shinefar
    pv2.type: SF-M18/144550
    pv3.manufacturer: Shinefar
    pv3.type: SF-M18/144550
    pv4.manufacturer: Shinefar
    pv4.type: SF-M18/144550
```

**Note**: _This is just an example, you need to replace the values with your own!_

## MQTT settings

By default, this add-on requires no `mqtt` config from the user. **This is not an error!**

However, you are free to set them if you want to override, however, in
general usage, that should not be needed and is not recommended for this add-on.

## Changelog & Releases

This repository keeps a change log using [GitHub's releases][releases]
functionality.

Releases are based on [Semantic Versioning][semver], and use the format
of `MAJOR.MINOR.PATCH`. In a nutshell, the version will be incremented
based on the following:

- `MAJOR`: Incompatible or major changes.
- `MINOR`: Backwards-compatible new features and enhancements.
- `PATCH`: Backwards-compatible bugfixes and package updates.

## Support

Got questions?

You have several options to get them answered:

- The Discussions section on [GitHub][discussions].
- The [Home Assistant Discord chat server][discord-ha] for general Home
  Assistant discussions and questions.

You could also [open an issue here][issue] GitHub.

## Authors & contributors

The original setup of this repository is by [Stefan Allius][author].

We're very happy to receive contributions to this project! You can get started by reading [CONTRIBUTING.md][contribute].

## License

This project is licensed under the [BSD 3-clause License][bsd].

Note the aiomqtt library used is based on the paho-mqtt library, which has a dual license.
One of the licenses is the so-called [Eclipse Distribution License v1.0.][eclipse]
It is almost word-for-word identical to the BSD 3-clause License. The only differences are:

- One use of "COPYRIGHT OWNER" (EDL) instead of "COPYRIGHT HOLDER" (BSD)
- One use of "Eclipse Foundation, Inc." (EDL) instead of "copyright holder" (BSD)

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

[tsunproxy]: https://github.com/s-allius/tsun-gen3-proxy
[discussions]: https://github.com/s-allius/tsun-gen3-proxy/discussions
[author]: https://github.com/s-allius
[discord-ha]: https://discord.gg/c5DvZ4e
[issue]: https://github.com/s-allius/tsun-gen3-proxy/issues
[releases]: https://github.com/s-allius/tsun-gen3-proxy/releases
[contribute]: https://github.com/s-allius/tsun-gen3-proxy/blob/main/CONTRIBUTING.md
[semver]: http://semver.org/spec/v2.0.0.htm
[bsd]: https://opensource.org/licenses/BSD-3-Clause
[eclipse]: https://www.eclipse.org/org/documents/edl-v10.php
[Mosquitto]: https://github.com/home-assistant/addons/blob/master/mosquitto/DOCS.md
[AdGuard]: https://github.com/hassio-addons/addon-adguard-home
[repository-badge]: https://img.shields.io/badge/Add%20repository%20to%20my-Home%20Assistant-41BDF5?logo=home-assistant&style=for-the-badge
[repository-url]: https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fs-allius%2Fha-addons
