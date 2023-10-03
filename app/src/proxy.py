import asyncio, logging, traceback
from async_stream import AsyncStream

class Proxy:
    def __init__ (proxy, reader, writer, addr):
        proxy.ServerStream = AsyncStream(proxy, reader, writer, addr)
        proxy.ClientStream = None

    async def server_loop(proxy, addr):
        logging.info(f'Accept connection from {addr}')        
        await proxy.ServerStream.loop()
        logging.info(f'Close server connection {addr}')
        
        if proxy.ClientStream:
            logging.debug ("close client connection")
            proxy.ClientStream.close()
        
    async def client_loop(proxy, addr):
        await proxy.ClientStream.loop()    
        logging.info(f'Close client connection {addr}')
        proxy.ServerStream.remoteStream = None
        proxy.ClientStream = None
        
    async def CreateClientStream (proxy, stream, host, port):
        addr = (host, port)
            
        try:
            logging.info(f'Connected to {addr}')
            connect = asyncio.open_connection(host, port)
            reader, writer = await connect    
            proxy.ClientStream = AsyncStream(proxy, reader, writer, addr, stream, server_side=False)
            asyncio.create_task(proxy.client_loop(addr))
            
        except ConnectionRefusedError as error:
            logging.info(f'{error}')
        except Exception:
            logging.error(
                f"Proxy: Exception for {addr}:\n"
                f"{traceback.format_exc()}")
        return proxy.ClientStream
        
    def __del__ (proxy):
        logging.debug ("Proxy __del__")