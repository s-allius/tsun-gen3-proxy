import logging

if __name__ == "app.src.gen3plus.connection_g3p":
    from app.src.gen3plus.solarman_v5 import SolarmanV5
else:  # pragma: no cover
    from gen3plus.solarman_v5 import SolarmanV5

logger = logging.getLogger('conn')


class ConnectionG3P(SolarmanV5):
    def __init__(self, addr, ifc, server_side,
                 client_mode: bool = False) -> None:
        super().__init__(addr, server_side, client_mode, ifc)

    def close(self):
        super().close()
        #  logger.info(f'AsyncStream refs: {gc.get_referrers(self)}')
