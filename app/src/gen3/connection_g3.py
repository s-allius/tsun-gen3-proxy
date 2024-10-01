import logging

if __name__ == "app.src.gen3.connection_g3":
    from app.src.gen3.talent import Talent
else:  # pragma: no cover
    from gen3.talent import Talent

logger = logging.getLogger('conn')


class ConnectionG3(Talent):
    def __init__(self, addr, ifc, server_side, id_str=b'') -> None:
        super().__init__(addr, server_side, ifc, id_str)
