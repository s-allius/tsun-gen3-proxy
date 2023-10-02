import asyncio, logging, traceback, weakref
from async_stream import AsyncStream

class Proxy:
    def __init__ (proxy, reader, writer, addr):
        proxy.__ServerStream = AsyncStream(proxy, reader, writer, addr)
        proxy.__ClientStream = None

    async def server_loop(proxy, addr):
        logging.info(f'Accept connection from {addr}')        
        await proxy.__ServerStream.loop()
        logging.info(f'Stopped server connection loop {addr}')
        
        if proxy.__ClientStream:
            logging.debug ("disconnect client connection")
            proxy.__ClientStream.disc()
        
    async def client_loop(proxy, addr):
        await proxy.__ClientStream.loop()    
        logging.info(f'Stopped client connection loop {addr}')
        proxy.__ClientStream = None
        
    async def CreateClientStream (proxy, host, port):
        addr = (host, port)
            
        try:
            logging.info(f'Connected to {addr}')
            connect = asyncio.open_connection(host, port)
            reader, writer = await connect    
            proxy.__ClientStream = AsyncStream(proxy, reader, writer, addr, weakref.ref(proxy.__ServerStream), server_side=False)
            asyncio.create_task(proxy.client_loop(addr))
            
        except ConnectionRefusedError as error:
            logging.info(f'{error}')
        except Exception:
            logging.error(
                f"Proxy: Exception for {addr}:\n"
                f"{traceback.format_exc()}")
        return weakref.ref(proxy.__ClientStream)
        
    def __del__ (proxy):
        logging.info ("Proxy __del__")