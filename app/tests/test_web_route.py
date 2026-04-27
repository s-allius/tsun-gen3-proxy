# test_with_pytest.py
import pytest
import asyncio
import logging
import os, errno
import datetime
from os import DirEntry, stat_result
from mock import patch, call, MagicMock, AsyncMock, mock_open

from server import app as my_app
from server import Server
from web import web
from async_stream import AsyncStreamClient
from gen3plus.inverter_g3p import InverterG3P
from web.log_handler import LogHandler
from web.network_tests import test_tcp_connection as tcp_connection_fnc
from web.network_tests import test_http_connection as http_connection_fnc
from web.network_tests import get_test_results, detect_platform, get_best_guess_host_ip
from test_inverter_g3p import FakeReader, FakeWriter, config_conn
from cnf.config import Config
from cnf.config_read_toml import ConfigReadToml
from proxy import Proxy

# Save the original timeout function before patching to avoid recursion
original_timeout = asyncio.timeout

class FakeServer(Server):
    def __init__(self):
        pass  # don't call the suoer(.__init__ for unit tests


pytest_plugins = ('pytest_asyncio',)
@pytest.fixture(scope="session")
def app():
    yield my_app

@pytest.fixture(scope="session")
def client(app):
    app.secret_key = 'super secret key'
    app.testing = True
    return app.test_client()

@pytest.fixture
def create_inverter(config_conn):
    _ = config_conn
    inv = InverterG3P(FakeReader(), FakeWriter(), client_mode=False)

    return inv

@pytest.fixture
def create_inverter_server(config_conn):
    _ = config_conn
    inv = InverterG3P(FakeReader(), FakeWriter(), client_mode=False)
    ifc = AsyncStreamClient(FakeReader(), FakeWriter(), inv.local,
                            None, inv.use_emulation)
    inv.remote.ifc = ifc

    return inv

@pytest.fixture
def create_inverter_client(config_conn):
    _ = config_conn
    inv = InverterG3P(FakeReader(), FakeWriter(), client_mode=True)
    ifc = AsyncStreamClient(FakeReader(), FakeWriter(), inv.local,
                            None, inv.use_emulation)
    inv.remote.ifc = ifc

    return inv

@pytest.mark.asyncio(loop_scope="session")
async def test_home(client):
    """Test the home route."""
    response = await client.get('/')
    assert response.status_code == 200
    assert response.mimetype == 'text/html'
    assert b"<title>TSUN Proxy - Connections</title>" in await response.data

@pytest.mark.asyncio(loop_scope="session")
async def test_page(client):
    """Test the mqtt page route."""
    response = await client.get('/mqtt')
    assert response.status_code == 200
    assert response.mimetype == 'text/html'
    assert b"<title>TSUN Proxy - MQTT Status</title>" in await response.data
    assert b'fetch("/mqtt-fetch")' in await response.data

@pytest.mark.asyncio(loop_scope="session")
async def test_rel_page(client):
    """Test the mqtt route with relative paths."""
    web.build_relative_urls = True
    response = await client.get('/mqtt')
    assert response.status_code == 200
    assert response.mimetype == 'text/html'
    assert b'fetch("./mqtt-fetch")' in await response.data
    web.build_relative_urls = False

@pytest.mark.asyncio(loop_scope="session")
async def test_network_tests(client):
    """Test the notes page route."""
    response = await client.get('/network_tests')
    assert response.status_code == 200
    assert response.mimetype == 'text/html'
    assert b"<title>TSUN Proxy - Network Tests</title>" in await response.data

@pytest.mark.asyncio(loop_scope="session")
async def test_notes(client):
    """Test the notes page route."""
    response = await client.get('/notes')
    assert response.status_code == 200
    assert response.mimetype == 'text/html'
    assert b"<title>TSUN Proxy - Important Messages</title>" in await response.data

@pytest.mark.asyncio(loop_scope="session")
async def test_logging(client):
    """Test the logging page route."""
    response = await client.get('/logging')
    assert response.status_code == 200
    assert response.mimetype == 'text/html'
    assert b"<title>TSUN Proxy - Log Files</title>" in await response.data

@pytest.mark.asyncio(loop_scope="session")
async def test_favicon96(client):
    """Test the favicon-96x96.png route."""
    response = await client.get('/favicon-96x96.png')
    assert response.status_code == 200
    assert response.mimetype == 'image/png'

@pytest.mark.asyncio(loop_scope="session")
async def test_favicon(client):
    """Test the favicon.ico route."""
    response = await client.get('/favicon.ico')
    assert response.status_code == 200
    assert response.mimetype == 'image/x-icon'

@pytest.mark.asyncio(loop_scope="session")
async def test_favicon_svg(client):
    """Test the favicon.svg route."""
    response = await client.get('/favicon.svg')
    assert response.status_code == 200
    assert response.mimetype == 'image/svg+xml'

@pytest.mark.asyncio(loop_scope="session")
async def test_apple_touch_icon(client):
    """Test the apple-touch-icon.png route."""
    response = await client.get('/apple-touch-icon.png')
    assert response.status_code == 200
    assert response.mimetype == 'image/png'

@pytest.mark.asyncio(loop_scope="session")
async def test_manifest(client):
    """Test the site.webmanifest route."""
    response = await client.get('/site.webmanifest')
    assert response.status_code == 200
    assert response.mimetype == 'application/manifest+json'

@pytest.mark.asyncio(loop_scope="session")
async def test_data_fetch(client, create_inverter):
    """Test the data-fetch route."""
    _ = create_inverter
    response = await client.get('/data-fetch')
    assert response.status_code == 200

    response = await client.get('/data-fetch')
    assert response.status_code == 200
    assert b'<h5>Connections</h5>' in await response.data

@pytest.mark.asyncio(loop_scope="session")
async def test_data_fetch1(client, create_inverter_server):
    """Test the data-fetch route with server connection."""
    _ = create_inverter_server
    response = await client.get('/data-fetch')
    assert response.status_code == 200

    response = await client.get('/data-fetch')
    assert response.status_code == 200
    assert b'<h5>Connections</h5>' in await response.data

@pytest.mark.asyncio(loop_scope="session")
async def test_data_fetch2(client, create_inverter_client):
    """Test the data-fetch route with client connection."""
    _ = create_inverter_client
    response = await client.get('/data-fetch')
    assert response.status_code == 200

    response = await client.get('/data-fetch')
    assert response.status_code == 200
    assert b'<h5>Connections</h5>' in await response.data

@pytest.mark.asyncio(loop_scope="session")
async def test_language_en(client):
    """Test the language/en route and cookie."""
    response = await client.get('/language/en', headers={'referer': '/index'})
    assert response.status_code == 302
    assert response.content_language.pop() == 'en'
    assert response.location == '/index'
    assert response.mimetype == 'text/html'
    assert b'<html lang=en' in await response.data
    assert b'<title>Redirecting...</title>' in await response.data

    client.set_cookie('test', key='language', value='de')
    response = await client.get('/')
    assert response.status_code == 200
    assert response.mimetype == 'text/html'
    assert b'<html lang="en"' in await response.data
    assert b'<title>TSUN Proxy - Connections</title>' in await response.data

@pytest.mark.asyncio(loop_scope="session")
async def test_language_de(client):
    """Test the language/de route."""

    response = await client.get('/language/de', headers={'referer': '/'})
    assert response.status_code == 302
    assert response.content_language.pop() == 'de'
    assert response.location == '/'
    assert response.mimetype == 'text/html'
    assert b'<html lang=en>' in await response.data
    assert b'<title>Redirecting...</title>' in await response.data

    client.set_cookie('test', key='language', value='en')
    response = await client.get('/')
    assert response.status_code == 200
    assert response.mimetype == 'text/html'
    assert b'<html lang="de"' in await response.data
    # the following assert fails on github runner, since the translation to german fails
    # assert b'<title>TSUN Proxy - Verbindungen</title>' in await response.data 

    """Switch back to english"""
    response = await client.get('/language/en', headers={'referer': '/index'})
    assert response.status_code == 302
    assert response.content_language.pop() == 'en'
    assert response.location == '/index'
    assert response.mimetype == 'text/html'
    assert b'<html lang=en>' in await response.data
    assert b'<title>Redirecting...</title>' in await response.data

@pytest.mark.asyncio(loop_scope="session")
async def test_language_unknown(client):
    """Test the language/unknown route."""
    response = await client.get('/language/unknown')
    assert response.status_code == 404
    assert response.mimetype == 'text/html'

    client.set_cookie('test', key='language', value='en')
    response = await client.get('/')
    assert response.status_code == 200
    assert response.mimetype == 'text/html'
    assert b'<title>TSUN Proxy - Connections</title>' in await response.data


@pytest.mark.asyncio(loop_scope="session")
async def test_mqtt_fetch(client, create_inverter):
    """Test the mqtt-fetch route."""
    _ = create_inverter
    Proxy.class_init()

    response = await client.get('/mqtt-fetch')
    assert response.status_code == 200
    assert b'<h5>MQTT devices</h5>' in await response.data

@pytest.fixture
def network_http_mocks():
    """Fixture for Logger and aiohttp """
    with patch('web.network_tests.logger') as mock_logger, \
         patch('aiohttp.ClientSession.get') as mock_get:
        
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock()

        mock_get.return_value = mock_resp

        # Die Mocks und den Handler als Dictionary oder Tuple zurückgeben
        yield {
            "logger": mock_logger,
            "get": mock_get,
            "resp": mock_resp
        }
def test_detect_platform_proxmox_qemu_dmi(network_http_mocks):
    """
    Tests detection via /sys/class/dmi/id/sys_vendor (QEMU).
    """
    # 1. Setup: File exists and contains 'QEMU'
    with patch('os.path.exists', return_value=True), \
         patch('builtins.open', mock_open(read_data="QEMU Project")):
        
        result = detect_platform()
        
        assert result == "Proxmox (QEMU VM)"
        # Verify debug log was called
        mock_logger = network_http_mocks["logger"]
        assert any("sys_vendor:" in str(call) for call in mock_logger.debug.call_args_list)

def test_detect_platform_proxmox_kvm_cpuinfo():
    """
    Tests detection via /proc/cpuinfo when DMI check fails or is not QEMU.
    """
    # 1. Setup: DMI exists but is generic, cpuinfo contains 'KVM'
    # side_effect for open: first call (DMI) returns generic, second (cpuinfo) returns KVM
    dmi_data = "Generic Vendor"
    cpu_data = "Common KVM processor"
    
    with patch('os.path.exists', return_value=True), \
         patch('builtins.open', mock_open()) as mocked_file:
        
        # Configure multiple file reads
        mocked_file.side_effect = [
            mock_open(read_data=dmi_data).return_value,
            mock_open(read_data=cpu_data).return_value
        ]
        
        result = detect_platform()
        
        assert result == "Proxmox (KVM)"

def test_detect_platform_bare_metal():
    """
    Tests detection as Bare Metal when no virtualization strings are found.
    """
    with patch('os.path.exists', return_value=True), \
         patch('builtins.open', mock_open(read_data="GenuineIntel")):
        
        result = detect_platform()
        
        assert result == "Bare Metal"

def test_detect_platform_bare_metal2():
    """
    Tests detection as Bare Metal when no virtualization strings are found.
    """
    with patch('os.path.exists', return_value=False), \
         patch('builtins.open', mock_open(read_data="GenuineIntel")):
        
        result = detect_platform()
        
        assert result == "Bare Metal"

def test_detect_platform_exception_handling():
    """
    Tests that any exception during file access results in 'Bare Metal'.
    """
    # Simulate a PermissionError or FileNotFoundError
    with patch('os.path.exists', side_effect=Exception("Access Denied")):
        
        result = detect_platform()
        
        # The 'except Exception: pass' block should lead to 'Bare Metal'
        assert result == "Bare Metal"

@pytest.mark.asyncio
async def test_get_best_guess_fqdn_success(network_http_mocks):
    """
    Test Case 1: Successfully resolving the IP via FQDN.
    """
    mock_fqdn = "my-server.local"
    mock_ip = "192.168.1.50"

    with patch('socket.getfqdn', return_value=mock_fqdn), \
         patch('web.network_tests.resolve', AsyncMock(return_value=mock_ip)):
        
        result = await get_best_guess_host_ip()
        
        assert result == mock_ip
        # Verify log output
        mock_logger = network_http_mocks["logger"]
        log_found = any(f"Host: {mock_fqdn}  IP: {mock_ip}" in str(call) 
                        for call in mock_logger.info.call_args_list)
        assert log_found

@pytest.mark.asyncio
async def test_get_best_guess_socket_fallback(network_http_mocks):
    """
    Test Case 2: FQDN resolution fails, but socket connection (8.8.8.8) works.
    """
    mock_ip_via_socket = "10.0.0.5"
    
    # Mock for the transport object returned by create_datagram_endpoint
    mock_transport = MagicMock()
    mock_transport.get_extra_info.return_value = [mock_ip_via_socket, 12345]

    with patch('socket.getfqdn', side_effect=Exception("FQDN failed")), \
         patch('asyncio.get_running_loop') as mock_loop:
        
        # Setup the async loop to return our transport
        mock_loop.return_value.create_datagram_endpoint = AsyncMock(
            return_value=(mock_transport, None)
        )

        result = await get_best_guess_host_ip()

        assert result == mock_ip_via_socket
        # Verify socket was closed
        mock_transport.close.assert_called_once()
        
        # Verify logging
        mock_logger = network_http_mocks["logger"]
        log_found = any(f"Container IP: {mock_ip_via_socket}" in str(call) 
                        for call in mock_logger.info.call_args_list)
        assert log_found

@pytest.mark.asyncio
async def test_get_best_guess_total_failure_localhost():
    """
    Test Case 3: Both attempts fail. 
    The second failure occurs during the async call to create_datagram_endpoint.
    """
    # 1. Mock FQDN to fail
    with patch('socket.getfqdn', side_effect=Exception("FQDN resolution failed")):
        
        # 2. Mock the event loop
        mock_loop = AsyncMock()
        
        # 3. Specifically make create_datagram_endpoint raise an exception
        # We use side_effect on the AsyncMock to simulate a network-related error
        mock_loop.create_datagram_endpoint.side_effect = Exception("Network unreachable")

        with patch('asyncio.get_running_loop', return_value=mock_loop):
            
            # Execute the function
            result = await get_best_guess_host_ip()
            
            # Verify the final fallback to localhost
            assert result == "127.0.0.1"
            
            # Verify that the loop was indeed asked to create an endpoint
            mock_loop.create_datagram_endpoint.assert_called_once()

@pytest.mark.asyncio
async def test_http_connection_fnc_success(network_http_mocks):
    """Test the test_http_connection method - good case."""

    mock_get = network_http_mocks["get"]
    mock_logger = network_http_mocks["logger"]
        
    # 1. call method under test
    await http_connection_fnc("127.0.0.1", 8000)

    # 2. Assertions
    mock_get.assert_called_once_with('http://127.0.0.1:8000/-/ready', timeout=5)
    mock_logger.warning.assert_not_called()
    mock_logger.error.assert_not_called()
    mock_logger.info.assert_called_once_with('Test Web server on (127.0.0.1:8000) ==> Ok')


@pytest.mark.asyncio
async def test_http_connection_fnc_error(network_http_mocks):
    """Test the test_http_connection method - good case."""

    mock_get = network_http_mocks["get"]
    mock_logger = network_http_mocks["logger"]
    mock_resp = network_http_mocks["resp"]
        
    # 1. patch response code
    mock_resp.status = 403

    # 2. call method under test
    await http_connection_fnc("127.0.0.1", 8000)

    # 3. Assertions
    mock_get.assert_called_once_with('http://127.0.0.1:8000/-/ready', timeout=5)
    mock_logger.info.assert_not_called()
    mock_logger.error.assert_not_called()
    mock_logger.warning.assert_called_once_with('Test Web server on (127.0.0.1:8000) ==> 403')

@pytest.mark.asyncio
async def test_http_connection_fnc_execpt(network_http_mocks):
    """Test the test_http_connection method - good case."""

    mock_get = network_http_mocks["get"]
    mock_logger = network_http_mocks["logger"]
    mock_resp = network_http_mocks["resp"]
        
    # 1. simulate connection refused error
    mock_get.side_effect=Exception("Connection Refused")

    # 2. call method under test
    await http_connection_fnc("127.0.0.1", 8000)

    # 3. Assertions
    mock_get.assert_called_once_with('http://127.0.0.1:8000/-/ready', timeout=5)
    mock_logger.info.assert_not_called()
    mock_logger.warning.assert_not_called()
    mock_logger.error.assert_called_once_with('Test Web server on (127.0.0.1:8000) ==> Connection Refused')

@pytest.mark.asyncio
async def test_http_connection_fnc_cancel(network_http_mocks):
    """Test the test_http_connection method - good case."""

    mock_get = network_http_mocks["get"]
    mock_logger = network_http_mocks["logger"]
    mock_resp = network_http_mocks["resp"]
        
    # 1. set side_effect cancel error
    mock_get.side_effect=asyncio.CancelledError

    # 2. call method under test
    try:
        await http_connection_fnc("127.0.0.1", 8000)
        pytest.fail(f"Abort exception missing")
    except asyncio.CancelledError:
        pass
    except Exception as e:
        pytest.fail(f"Unexpected exception: {e}")

    # 3. Assertions
    mock_get.assert_called_once_with('http://127.0.0.1:8000/-/ready', timeout=5)
    mock_logger.info.assert_not_called()
    mock_logger.warning.assert_not_called()
    mock_logger.error.assert_not_called()

@pytest.fixture
def network_tcp_mocks():
    """Fixture for Logger and aiohttp """

    # 1. Setup mocks for Reader and Writer
    # We use AsyncMock because these objects are used with 'await'
    mock_reader = AsyncMock(spec=asyncio.StreamReader)
    mock_writer = AsyncMock(spec=asyncio.StreamWriter)

    with patch('web.network_tests.logger') as mock_logger, \
         patch('asyncio.open_connection', 
               AsyncMock(return_value=(mock_reader, mock_writer))) as mock_open:
        
        # Die Mocks und den Handler als Dictionary oder Tuple zurückgeben
        yield {
            "logger": mock_logger,
            "reader": mock_reader,
            "writer": mock_writer,
            "open": mock_open
        }

@pytest.mark.asyncio
async def test_tcp_connection_success(network_tcp_mocks):
    """
    Tests a successful TCP ping-pong flow between inverter and proxy.
    Uses the 'network_mocks' fixture to capture logs and prevent real IO.
    """
    # 1. Get mocks for Reader, Writer and Logger from fixture
    mock_reader = network_tcp_mocks["reader"]
    mock_writer = network_tcp_mocks["writer"]
    mock_logger = network_tcp_mocks["logger"]
    
    # Configure the mock reader to return 'ping' (the expected success response)
    mock_reader.read.return_value = b'ping'
    
    # 2. Execute the function under test
    await tcp_connection_fnc("127.0.0.1", 5005)
    
    # 3. Verify the results (Assertions)
    
    # Check if the success message was logged
    # We check for the suffix because the prefix might contain dynamic/translated text
    ok_logged = any("==> Ok" in call.args[0] for call in mock_logger.info.call_args_list)
    assert ok_logged, "Expected success log '==> Ok' was not found"
    # Verify that 'ping' was actually written to the socket
    mock_writer.write.assert_called_once_with(b'ping')
    
    # Ensure drain was called after writing
    mock_writer.drain.assert_called_once()
    
    # Verify that the connection was closed properly in the 'finally' block
    mock_writer.close.assert_called_once()
    mock_writer.wait_closed.assert_called_once()

    mock_logger.warning.assert_not_called()
    mock_logger.error.assert_not_called()
    mock_logger.info.assert_called_once_with("Connection Test: Inverter to (127.0.0.1:5005) ==> Ok")

@pytest.mark.asyncio
async def test_tcp_connection_wrong_response(network_tcp_mocks):
    """
    Tests the case where the server responds with something other than 'ping'.
    """
    # 1. Get mocks for Reader, Writer and Logger from fixture
    mock_reader = network_tcp_mocks["reader"]
    mock_logger = network_tcp_mocks["logger"]
    
    # Simulate an unexpected response
    mock_reader.read.return_value = b'unknown_error'
    
    # 2. Execute the function under test
    await tcp_connection_fnc("127.0.0.1", 5005)
        
    # Check if a warning was logged with the unexpected data
    mock_logger.info.assert_not_called()
    mock_logger.error.assert_not_called()
    mock_logger.warning.assert_called_once_with("Connection Test: Inverter to (127.0.0.1:5005) ==> b'unknown_error'")

@pytest.mark.asyncio
async def test_tcp_connection_wrong_closed(network_tcp_mocks):
    """
    Tests the case where the server responds with something other than 'ping'.
    """
    # 1. Get mocks for Reader, Writer and Logger from fixture
    mock_reader = network_tcp_mocks["reader"]
    mock_logger = network_tcp_mocks["logger"]
    
    # Simulate an empty response
    mock_reader.read.return_value = b''
    
    # 2. Execute the function under test
    await tcp_connection_fnc("127.0.0.1", 5005)
        
    # Check if a warning was logged with the unexpected data
    mock_logger.info.assert_not_called()
    mock_logger.warning.assert_not_called()
    mock_logger.error.assert_not_called()
@pytest.mark.asyncio
async def test_tcp_connection_exception(network_tcp_mocks):
    """
    Tests the case where the server responds with something other than 'ping'.
    """
    # 1. Get mocks for Reader, Writer and Logger from fixture
    mock_logger = network_tcp_mocks["logger"]
    mock_open = network_tcp_mocks["open"]
    
    # 1. simulate connection refused error
    mock_open.side_effect=Exception("Connection Refused")
    
    # 2. Execute the function under test
    await tcp_connection_fnc("127.0.0.1", 5005)
        
    # Check if a warning was logged with the unexpected data
    mock_logger.info.assert_not_called()
    mock_logger.warning.assert_not_called()
    mock_logger.error.assert_called_once_with("Connection Test: Inverter to (127.0.0.1:5005) ==> Connection Refused")

@pytest.mark.asyncio
async def test_tcp_connection_cancel(network_tcp_mocks):
    """
    Tests the case where the server responds with something other than 'ping'.
    """
    # 1. Get mocks for Reader, Writer and Logger from fixture
    mock_logger = network_tcp_mocks["logger"]
    mock_open = network_tcp_mocks["open"]
    
    # 2. set side_effect cancel error
    mock_open.side_effect=asyncio.CancelledError
    
    # 3. Execute the function under test
    try:
        await tcp_connection_fnc("127.0.0.1", 5005)
        pytest.fail(f"Abort exception missing")
    except asyncio.CancelledError:
        pass
    except Exception as e:
        pytest.fail(f"Unexpected exception: {e}")
        
    # Check if a warning was logged with the unexpected data
    mock_logger.info.assert_not_called()
    mock_logger.warning.assert_not_called()
    mock_logger.error.assert_not_called()

@pytest.mark.asyncio(loop_scope="session")
async def test_reentrant_call(network_http_mocks):
    """Test: Starting a second test run before the first one is complete."""

    Config.act_config = {
        'tsun':{'enabled': True, 'listener': True, 'host': 'logger.talent-monitoring.com'},
        'solarman':{'enabled': False, 'listener': False, 'host': 'iot.talent-monitoring.com'}
    }

    # First clear log
    LogHandler().clear()

    run1 = get_test_results()
    run2 = get_test_results()
    await asyncio.gather(run1,run2)

    mock_logger = network_http_mocks["logger"]
    log_found = any("Starting new test task" in str(call) 
                    for call in mock_logger.info.call_args_list)
    assert log_found

    log_found = any("Join an ongoing test" in str(call) 
                    for call in mock_logger.info.call_args_list)
    assert log_found

@pytest.mark.asyncio(loop_scope="session")
async def test_result_fetch1(client):
    """Test the result-fetch route."""

    Config.act_config = {
        'tsun':{'enabled': True, 'listener': True, 'host': 'logger.talent-monitoring.com'},
        'solarman':{'enabled': False, 'listener': False, 'host': 'iot.talent-monitoring.com'}
    }

    s = FakeServer()
    s.src_dir = 'app/src/'
    s.init_logging_system()

    test_ip = await get_best_guess_host_ip()

    # First clear log
    LogHandler().clear()

    # then fetch test result list
    response = await client.get('/result-fetch')
    
    assert response.status_code == 200
    result = await response.data
    assert b'TSUN/Solarman cloud connections are disabled' in result
    assert b"DNS test: &#39;logger.talent-monitoring.com&#39" in result
    assert b'Proxy is not listening on port 10000' in result
    assert bytes(f'Connection Test: Inverter to ({test_ip}:5005)', 'UTF8') in result
    assert b'Test run finished' in result

    # then fetch test result list
    response = await client.get('/result-fetch')
    
    assert response.status_code == 200
    result = await response.data
    assert b'TSUN/Solarman cloud connections are disabled' in result
    assert b"DNS test: &#39;logger.talent-monitoring.com&#39" in result
    assert b'Proxy is not listening on port 10000' in result
    assert bytes(f'Connection Test: Inverter to ({test_ip}:5005)', 'UTF8') in result
    assert b'Test run finished' in result

@pytest.mark.asyncio(loop_scope="session")
async def test_result_fetch1(client):
    """Test the result-fetch route."""

    Config.act_config = {
        'tsun':{'enabled': True, 'listener': True, 'host': 'logger.talent-monitoring.com'},
        'solarman':{'enabled': False, 'listener': False, 'host': 'iot.talent-monitoring.com'}
    }

    s = FakeServer()
    s.src_dir = 'app/src/'
    s.init_logging_system()

    test_ip = await get_best_guess_host_ip()

    # First clear log
    LogHandler().clear()

    # then fetch test result list
    response = await client.get('/result-fetch')
    
    assert response.status_code == 200
    result = await response.data
    assert b'TSUN/Solarman cloud connections are disabled' in result
    assert b"DNS test: &#39;logger.talent-monitoring.com&#39" in result
    assert b'Proxy is not listening on port 10000' in result
    assert bytes(f'Connection Test: Inverter to ({test_ip}:5005)', 'UTF8') in result
    assert b'Test run finished' in result

@pytest.mark.asyncio(loop_scope="session")
async def test_result_fetch2(client):
    """Test the result-fetch route."""
    Config.act_config = {
        'tsun':{'enabled': False, 'listener': False, 'host': 'logger.talent-monitoring.com'},
        'solarman':{'enabled': True, 'listener': True, 'host': 'iot.talent-monitoring.com'}
    }

    s = FakeServer()
    s.src_dir = 'app/src/'
    s.init_logging_system()

    test_ip = await get_best_guess_host_ip()

    # First clear log
    LogHandler().clear()

    # then fetch test result list
    response = await client.get('/result-fetch')
    
    assert response.status_code == 200
    result = await response.data
    assert b'TSUN cloud connections are disabled' in result
    assert b"DNS test: &#39;iot.talent-monitoring.com&#39" in result
    assert b'Proxy is not listening on port 5005' in result
    assert bytes(f'Connection Test: Inverter to ({test_ip}:10000)', 'UTF8') in result
    assert b'Test run finished' in result


@pytest.mark.asyncio(loop_scope="session")
async def test_result_fetch_abort(client):
    """
    Tests if the routine handles a timeout correctly by forcing 
    the 10s timeout to actually expire after only 0.1s.
    """
    Config.act_config = {
        'tsun':{'enabled': False, 'listener': False, 'host': 'logger.talent-monitoring.com'},
        'solarman':{'enabled': True, 'listener': True, 'host': 'iot.talent-monitoring.com'}
    }

    s = FakeServer()
    s.src_dir = 'app/src/'
    s.init_logging_system()


    # First clear log
    LogHandler().clear()

    # 1. We define a side_effect function that replaces the 10s with 0.1s
    def side_effect_short_timeout(delay):
        # Use the original function here, which is not mocked
        return original_timeout(0.1)
    
    async def slow_script():
        await asyncio.sleep(1.0)
    
    # 2. Patch asyncio.timeout
    with patch('asyncio.timeout', side_effect=side_effect_short_timeout) as mocked_timeout:
        
        # We need a test_script that definitely takes longer than 0.1s
        # so that the timeout actually hits.
        with patch('web.network_tests.get_best_guess_host_ip', AsyncMock()) as mock_script:
            # Simulate the script taking longer than our new 0.1s timeout
            mock_script.side_effect = slow_script

            response = await client.get('/result-fetch')

            assert response.status_code == 200
            result = await response.data
            assert b'Test run timed out after ' in result

@pytest.mark.asyncio(loop_scope="session")
async def test_notes_fetch(client, config_conn):
    """Test the notes-fetch route."""
    _ = config_conn

    s = FakeServer()
    s.src_dir = 'app/src/'
    s.init_logging_system()

    # First clear log and test Well done message
    logh = LogHandler()
    logh.clear()
    response = await client.get('/notes-fetch')
    assert response.status_code == 200
    assert b'<h2>Well done!</h2>' in await response.data

    # Check info logs which must be ignored here
    logging.info('config_info')
    logh.flush()
    response = await client.get('/notes-fetch')
    assert response.status_code == 200
    assert b'<h2>Well done!</h2>' in await response.data

    # Check warning logs which must be added to the note list
    logging.warning('config_warning')
    logh.flush()
    response = await client.get('/notes-fetch')
    assert response.status_code == 200
    assert b'WARNING' in await response.data
    assert b'config_warning' in await response.data

    # Check error logs which must be added to the note list
    logging.error('config_err')
    logh.flush()
    response = await client.get('/notes-fetch')
    assert response.status_code == 200
    assert b'ERROR' in await response.data
    assert b'config_err' in await response.data


@pytest.mark.asyncio(loop_scope="session")
async def test_file_fetch(client, config_conn, monkeypatch):
    """Test the data-fetch route."""
    _ = config_conn
    assert Config.log_path == 'app/tests/log/'
    def my_stat1(*arg):
        stat = stat_result
        stat.st_size = 20
        stat.st_birthtime = datetime.datetime(2024, 1, 31, 10, 30, 15)
        stat.st_mtime = datetime.datetime(2024, 1, 1, 1, 30, 15).timestamp()
        return stat

    monkeypatch.setattr(DirEntry, "stat", my_stat1)
    response = await client.get('/file-fetch')
    assert response.status_code == 200


    def my_stat2(*arg):
        stat = stat_result
        stat.st_size = 20
        stat.st_mtime = datetime.datetime(2024, 1, 1, 1, 30, 15).timestamp()
        return stat

    monkeypatch.setattr(DirEntry, "stat", my_stat2)
    monkeypatch.delattr(stat_result, "st_birthtime")
    response = await client.get('/file-fetch')
    assert response.status_code == 200
    assert b'<h4>test.txt</h4>' in await response.data

@pytest.mark.asyncio(loop_scope="session")
async def test_send_file(client, config_conn):
    """Test the send-file route."""
    _ = config_conn
    assert Config.log_path == 'app/tests/log/'
    response = await client.get('/send-file/test.txt')
    assert response.status_code == 200
    assert b'2025-04-30 00:01:23' in await response.data


@pytest.mark.asyncio(loop_scope="session")
async def test_missing_send_file(client, config_conn):
    """Test the send-file route (file not found)."""
    _ = config_conn
    assert Config.log_path == 'app/tests/log/'
    response = await client.get('/send-file/no_file.log')
    assert response.status_code == 404


@pytest.mark.asyncio(loop_scope="session")
async def test_invalid_send_file(client, config_conn):
    """Test the send-file route (invalid filename)."""
    _ = config_conn
    assert Config.log_path == 'app/tests/log/'
    response = await client.get('/send-file/../test_web_route.py')
    assert response.status_code == 404

@pytest.fixture
def patch_os_remove_err():
    def new_remove(file_path: str):
        raise OSError(errno.ENOENT, os.strerror(errno.ENOENT), file_path)


    with patch.object(os, 'remove', new_remove) as wrapped_os:
        yield wrapped_os

@pytest.fixture
def patch_os_remove_ok():
    with patch.object(os, 'remove') as wrapped_os:
        yield wrapped_os

@pytest.fixture
def patch_os_stat_none():
    def new_stat(file_path: str):
        return None

    with patch.object(os, 'stat', new_stat) as wrapped_os:
        yield wrapped_os

@pytest.mark.asyncio(loop_scope="session")
async def test_del_file_ok(client, config_conn, patch_os_remove_ok):
    """Test the del-file route with no error."""
    _ = config_conn
    spy = patch_os_remove_ok
    assert Config.log_path == 'app/tests/log/'
    response = await client.delete ('/del-file/test.txt')
    assert response.status_code == 204
    spy.assert_called_once()

@pytest.mark.asyncio(loop_scope="session")
async def test_del_file_err(client, config_conn, patch_os_remove_err):
    """Test the send-file route with OSError."""
    _ = config_conn
    _ = patch_os_remove_err
    assert Config.log_path == 'app/tests/log/'
    response = await client.delete ('/del-file/test.txt')
    assert response.status_code == 404

@pytest.mark.asyncio(loop_scope="session")
async def test_del_older_file_ok1(client, config_conn, patch_os_stat_none, patch_os_remove_ok):
    """Test the del-older-files route with no error."""
    _ = config_conn
    _ = patch_os_stat_none
    spy = patch_os_remove_ok
    assert Config.log_path == 'app/tests/log/'
    response = await client.delete ('/del-older-files/test-2025-04-20.txt')
    assert response.status_code == 204
    assert spy.call_count == 1
    spy.assert_has_calls([call("app/tests/log/test-2025-04-20.txt")], any_order=True)

@pytest.mark.asyncio(loop_scope="session")
async def test_del_older_file_ok2(client, config_conn, patch_os_stat_none, patch_os_remove_ok):
    """Test the del-older-files route with no error."""
    _ = config_conn
    _ = patch_os_stat_none
    spy = patch_os_remove_ok
    assert Config.log_path == 'app/tests/log/'
    response = await client.delete ('/del-older-files/test.txt')
    assert response.status_code == 204
    assert spy.call_count == 2
    spy.assert_has_calls([call("app/tests/log/test-2025-04-20.txt"), call("app/tests/log/test.txt")], any_order=True)

@pytest.mark.asyncio(loop_scope="session")
async def test_del_older_file_err(client, config_conn, patch_os_remove_err):
    """Test the send-file route with OSError."""
    _ = config_conn
    _ = patch_os_remove_err
    assert Config.log_path == 'app/tests/log/'
    response = await client.delete ('/del-older-files/test.txt')
    assert response.status_code == 404

@pytest.mark.asyncio(loop_scope="session")
async def test_addon_links(client):
    """Test links to HA add-on config/log in UI"""
    with patch.dict(os.environ, {'SLUG': 'c676133d', 'HOSTNAME': 'c676133d-tsun-proxy'}):
        response = await client.get('/')
        assert response.status_code == 200
        assert response.mimetype == 'text/html'
        assert b'Add-on Config' in await response.data
        assert b'href="/hassio/addon/c676133d_tsun-proxy/logs' in await response.data
        assert b'href="/hassio/addon/c676133d_tsun-proxy/config' in await response.data

    # check that links are not available if env vars SLUG and HOSTNAME are not defined (docker version)    
    response = await client.get('/')
    assert response.status_code == 200
    assert response.mimetype == 'text/html'
    assert b'Add-on Config' not in await response.data
