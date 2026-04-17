from quart_babel import format_datetime
import os
import re
import socket
import aiohttp
import logging
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
    if False:  # SUPERVISOR_TOKEN:
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
    platform = detect_platform()
    logger.info(f"platform: {platform}")
    host_ip = await get_best_guess_host_ip()
    logger.info(f"host_ip: {host_ip}")

    return await render_template(
        'page_network_tests.html.j2',
        fetch_url=url_for('.result_fetch'))
