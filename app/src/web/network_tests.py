import asyncio
import os
import re
import socket
import aiohttp
import logging
from quart_babel import format_datetime
from quart import render_template
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
    test_url = f"http://{host_ip}:{port}/-/health"

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(test_url, timeout=5) as resp:
                if resp.status == 200:
                    logger.info(f"HTTP Connection {host_ip}:{port}")
                else:
                    logger.warning(f"HTTP Connection {host_ip}:{port}"
                                   f" ==> {resp.status}")
                return
        except Exception as e:
            logger.error(f"HTTP Connection {host_ip}:{port} ==> {e}")


async def test_tcp_connection(host_ip, port):
    # Verbindung asynchron aufbauen

    try:
        reader, writer = await asyncio.open_connection(host_ip, port)
        logger.debug("TCP Connection to {host_ip}:{port} established")
        # Daten senden
        writer.write(b'ping')
        await writer.drain()  # Warten, bis der Puffer geleert is
        # Daten empfangen (bis zu 255 Bytes)
        response = await reader.read(255)
        if not response:
            logger.debug(f"TCP Connection {host_ip}:{port}"
                         " ==> closed by server")
        elif response == b'ping':
            logger.info(f"TCP Connection {host_ip}:{port} ==> Ok")
        else:
            logger.warning(f"TCP Connection {host_ip}:{port} ==> {response}")

    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.error(f"TCP Connection {host_ip}:{port} ==> {e}")
    finally:
        logger.debug("TCP Connection to {host_ip}:{port} closing...")
        writer.close()
        await writer.wait_closed()


async def test_script() -> None:
    # clear result table in the web UI
    TestHandler().clear()

    platform = detect_platform()
    logger.info(f"platform: {platform}")
    host_ip = await get_best_guess_host_ip()
    logger.info(f"host_ip: {host_ip}")
    await test_http_connection(host_ip, 8127)
    await test_tcp_connection(host_ip, 5005)
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
