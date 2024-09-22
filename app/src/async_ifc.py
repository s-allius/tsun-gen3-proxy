if __name__ == "app.src.async_ifc":
    from app.src.byte_fifo import ByteFifo
else:  # pragma: no cover
    from byte_fifo import ByteFifo


class AsyncIfc():
    def __init__(self):
        self.read = ByteFifo()
        self.write = ByteFifo()
        self.forward = ByteFifo()
