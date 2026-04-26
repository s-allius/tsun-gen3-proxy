import asyncio
import os
import socket
import aiohttp
import logging
from quart_babel import format_datetime, _
from quart import render_template
from cnf.config import Config
from .wrapper import url_for

from . import web
from .log_handler import TestHandler

logger = logging.getLogger('test')


def detect_platform():
    """Checks for Proxmox/KVM or physical hardware."""
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
    """Try to find the LAN IP (Hostname -> Socket)."""
    loop = asyncio.get_running_loop()

    # 1. Try: Resolve the default hostname (this often works on bare metal)
    try:
        fqdn = socket.getfqdn()
        container_ip = await resolve(fqdn)
        logger.info(f"Host: {fqdn}  IP: {container_ip}")
        return container_ip

    except Exception:
        pass

    # 2. Try: Guessing your own LAN IP address via an outgoing connection
    try:
        transport, _ = await loop.create_datagram_endpoint(
            asyncio.DatagramProtocol,
            remote_addr=('8.8.8.8', 80)
        )
        container_ip = transport.get_extra_info('sockname')[0]
        transport.close()
        logger.info(f"Container IP: {container_ip}")

        return container_ip

    except Exception:
        return "127.0.0.1"


async def test_http_connection(host_ip, port):
    """Attempts to establish an HTTP connection to
    the proxy and logs the result to the logger."""
    test_url = f"http://{host_ip}:{port}/-/ready"
    test_txt = f"{_('Test Web server on')} ({host_ip}:{port}) "

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
    """Attempts to establish a TCP connection to
    the proxy like a inverter and logs the result to the logger."""
    test_txt = f"{_('Connection Test: Inverter to')} ({host_ip}:{port}) "
    try:
        reader, writer = await asyncio.open_connection(host_ip, port)
        logger.debug(f"{test_txt}established")
        # send the magic word 'ping' to the proxy and await the response
        writer.write(b'ping')
        await writer.drain()  # Warten, bis der Puffer geleert is
        # Daten empfangen (bis zu 255 Bytes)
        response = await reader.read(255)
        if not response:
            logger.debug(f"{test_txt}==> closed by server")
        elif response == b'ping':
            # The proxy response is "ping" and indicates
            # that it comes from the proxy
            logger.info(f"{test_txt}==> Ok")
        else:
            logger.warning(f"{test_txt}==> {response}")

    except asyncio.CancelledError:
        raise
    except Exception as e:
        logger.error(f"{test_txt}==> {e}")
    finally:
        logger.debug(f"{test_txt}closing...")
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass


async def resolve(host):
    """Resolves a FQDN to an ip address"""
    loop = asyncio.get_running_loop()
    info = await loop.getaddrinfo(host, None, family=socket.AF_INET)
    return info[0][4][0]


async def test_script() -> None:
    # clear result table in the web UI
    TestHandler().clear()
    config_tsun = Config.get('tsun')
    config_solarman = Config.get('solarman')

    platform = detect_platform()
    logger.info(f"Platform: {platform}")

    # forwarding for port 5005 enabled?
    #  then check DNS resolution for TSUN cloud
    if not config_tsun['enabled']:
        logger.info(_("TSUN cloud connections are disabled,"
                    " skip the DNS resolution test"))
    else:
        host = config_tsun['host']
        ip = await resolve(host)
        logger.info(f"DNS test: '{host}' {_("resolved to")}"
                    f" {ip} ==> Ok")

    # forwarding for port 10000 enabled?
    #  then check DNS resolution for Solarman cloud
    if not config_solarman['enabled']:
        logger.info(_("TSUN/Solarman cloud connections are disabled,"
                    " skip the DNS resolution test"))
    else:
        host = config_solarman['host']
        ip = await resolve(host)
        logger.info(f"DNS test: '{host}' {_("resolved to")}"
                    f" {ip} ==> Ok")

    # determine host ip of the proxy
    host_ip = await get_best_guess_host_ip()
    await test_http_connection(host_ip, 8127)

    # listening for port 5005 enabled?
    if not config_tsun['listener']:
        logger.info(_("Proxy is not listening on port 5005,"
                    " skip the inverter connect test"))
    else:
        await test_tcp_connection(host_ip, 5005)

    # listening for port 10000 enabled?
    if not config_solarman['listener']:
        logger.info(_("Proxy is not listening on port 10000,"
                    " skip the inverter connect test"))
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
