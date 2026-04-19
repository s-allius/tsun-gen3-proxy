import asyncio
import os
import re
import socket
import aiohttp
import logging
from quart_babel import format_datetime
from quart import render_template
from cnf.config import Config
from .wrapper import url_for

from . import web
from .log_handler import TestHandler

logger = logging.getLogger('test')
SUPERVISOR_TOKEN = os.getenv("SUPERVISOR_TOKEN")


def detect_platform():
    """Prüft auf Proxmox/KVM oder echte Hardware."""
    try:
        if os.path.exists("/sys/class/dmi/id/sys_vendor"):
            with open("/sys/class/dmi/id/sys_vendor", "r") as f:
                sys_vendor = f.read()
                logger.debug(f"sys_vendor:\n{sys_vendor}")
                if "QEMU" in sys_vendor:
                    return "Proxmox (QEMU VM)"
        with open("/proc/cpuinfo", "r") as f:
            cpuinfo = f.read()
            logger.debug(f"cpuinfo:\n{cpuinfo}")
            if "QEMU" in cpuinfo or "KVM" in cpuinfo:
                return "Proxmox (KVM)"
    except Exception:
        pass
    return "Bare Metal"


async def get_best_guess_host_ip():
    """Versucht die LAN-IP zu finden (HA API -> Hostname -> Socket)."""
    # 1. Versuch: Home Assistant Supervisor API
    if SUPERVISOR_TOKEN:
        url = "http://supervisor/core/api/config"
        headers = {"Authorization": f"Bearer {SUPERVISOR_TOKEN}"}
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=headers,
                                       timeout=2) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        match = re.search(r'https?://([^:/\s]+)',
                                          data.get("internal_url", ""))
                        if match:
                            return match.group(1)
            except Exception:
                pass

    # 2. Versuch: Standard-Hostname auflösen (funktioniert oft auf Bare Metal)
    try:
        return socket.getfqdn()
    except Exception:
        pass

    # 3. Versuch: Über eine ausgehende Verbindung die eigene LAN-IP raten
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


async def test_http_connection(host_ip, port):

    # Der Test-Link nutzt die ermittelte LAN-IP
    test_url = f"http://{host_ip}:{port}/-/ready"
    test_txt = f"Test Web server on ({host_ip}:{port}) "

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(test_url, timeout=5) as resp:
                if resp.status == 200:
                    logger.info(f"{test_txt}==> Ok")
                else:
                    logger.warning(f"{test_txt}==> {resp.status}")
                return
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"{test_txt}==> {e}")


async def test_tcp_connection(host_ip, port):
    # Verbindung asynchron aufbauen
    test_txt = f"Connect Test: Inverter to ({host_ip}:{port}) "
    try:
        reader, writer = await asyncio.open_connection(host_ip, port)
        logger.debug(f"{test_txt}established")
        # Daten senden
        writer.write(b'ping')
        await writer.drain()  # Warten, bis der Puffer geleert is
        # Daten empfangen (bis zu 255 Bytes)
        response = await reader.read(255)
        if not response:
            logger.debug(f"{test_txt}==> closed by server")
        elif response == b'ping':
            logger.info(f"{test_txt}==> Ok")
        else:
            logger.warning(f"{test_txt}==> {response}")

    except asyncio.CancelledError:
        raise
    except Exception as e:
        logger.error(f"{test_txt}==> {e}")
    finally:
        logger.debug(f"{test_txt}closing...")
        writer.close()
        await writer.wait_closed()


async def resolve(host):
    loop = asyncio.get_running_loop()
    # Nutzt einen Threadpool im Hintergrund
    info = await loop.getaddrinfo(host, None, family=socket.AF_INET)
    return info[0][4][0]


async def test_script() -> None:
    # clear result table in the web UI
    TestHandler().clear()
    config_tsun = Config.get('tsun')
    config_solarman = Config.get('solarman')

    platform = detect_platform()
    logger.info(f"platform: {platform}")

    # forwarding for port 5005 enabled?
    #  then check DNS resolution for TSUN cloud
    if not config_tsun['enabled']:
        logger.info("TSUN cloud connections are disabled,"
                    " skip the DNS resolution test")
    else:
        host = config_tsun['host']
        ip = await resolve(host)
        logger.info(f"DNS test: '{host}' resolved to {ip} ==> Ok")

    # forwarding for port 10000 enabled?
    #  then check DNS resolution for Solarman cloud
    if not config_solarman['enabled']:
        logger.info("TSUN/Solarman cloud connections are disabled,"
                    " skip the DNS resolution test")
    else:
        host = config_solarman['host']
        ip = await resolve(host)
        logger.info(f"DNS test: '{host}' resolved to {ip} ==> Ok")

    # check internet access and make a tracert

    host_ip = await get_best_guess_host_ip()
    logger.info(f"host_ip: {host_ip}")
    await test_http_connection(host_ip, 8127)

    # listening for port 5005 enabled?
    if not config_tsun['listener']:
        logger.info("Proxy is not listening on port 5005,"
                    " skip the inverter connect test")
    else:
        await test_tcp_connection(host_ip, 5005)

    # listening for port 10000 enabled?
    if not config_solarman['listener']:
        logger.info("Proxy is not listening on port 10000,"
                    " skip the inverter connect test")
    else:
        await test_tcp_connection(host_ip, 10000)


@web.route('/result-fetch')
async def result_fetch():
    data = {
        "update-time": format_datetime(format="medium"),
    }
    data["result-list"] = await render_template(
        'templ_result_list.html.j2',
        results=TestHandler().get_buffer())

    return data


@web.route('/network_tests')
async def network_tests():
    loop = asyncio.get_event_loop()
    loop.create_task(test_script())

    return await render_template(
        'page_network_tests.html.j2',
        fetch_url=url_for('.result_fetch'))
