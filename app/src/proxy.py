import asyncio, logging, traceback
from async_stream import AsyncStream

class Proxy:
    def __init__ (proxy, reader, writer, addr):
        proxy.ServerStream = AsyncStream(proxy, reader, writer, addr)
        proxy.ClientStream = None

    async def server_loop(proxy, addr):
        '''Loop for receiving messages from the inverter (server-side)'''
        logging.info(f'Accept connection from  {addr}')        
        await proxy.ServerStream.loop()
        logging.info(f'Server loop stopped for {addr}')
        
        # if the server connection closes, we also disconnect the connection to te TSUN cloud
        if proxy.ClientStream:
            logging.debug ("disconnect client connection")
            proxy.ClientStream.disc()
        
    async def client_loop(proxy, addr):
        '''Loop for receiving messages from the TSUN cloud (client-side)'''
        await proxy.ClientStream.loop()    
        logging.info(f'Client loop stopped for {addr}')

        # if the client connection closes, we don't touch the server connection. Instead we erase the client
        # connection stream, thus on the next received packet from the inverter, we can establish a new connection 
        # to the TSUN cloud
        proxy.ClientStream = None
        
    async def CreateClientStream (proxy, stream, host, port):
        '''Establish a client connection to the TSUN cloud'''
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