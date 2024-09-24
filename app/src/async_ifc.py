from abc import ABC, abstractmethod


class AsyncIfc(ABC):
    @abstractmethod
    def get_conn_no(self):
        pass  # pragma: no cover

    @abstractmethod
    def set_node_id(self, value: str):
        pass  # pragma: no cover

    #
    #  TX - QUEUE
    #
    @abstractmethod
    def tx_add(self, data: bytearray):
        ''' add data to transmit queue'''
        pass  # pragma: no cover

    @abstractmethod
    def tx_flush(self):
        ''' send transmit queue and clears it'''
        pass  # pragma: no cover

    @abstractmethod
    def tx_get(self, size: int = None) -> bytearray:
        '''removes size numbers of bytes and return them'''
        pass  # pragma: no cover

    @abstractmethod
    def tx_peek(self, size: int = None) -> bytearray:
        '''returns size numbers of byte without removing them'''
        pass  # pragma: no cover

    @abstractmethod
    def tx_log(self, level, info):
        ''' log the transmit queue'''
        pass  # pragma: no cover

    @abstractmethod
    def tx_clear(self):
        ''' clear transmit queue'''
        pass  # pragma: no cover

    @abstractmethod
    def tx_len(self):
        ''' get numner of bytes in the transmit queue'''
        pass  # pragma: no cover

    #
    #  FORWARD - QUEUE
    #
    @abstractmethod
    def fwd_add(self, data: bytearray):
        ''' add data to forward queue'''
        pass  # pragma: no cover

    @abstractmethod
    def fwd_flush(self):
        ''' send forward queue and clears it'''
        pass  # pragma: no cover

    @abstractmethod
    def fwd_log(self, level, info):
        ''' log the forward queue'''
        pass  # pragma: no cover

    @abstractmethod
    def fwd_clear(self):
        ''' clear forward queue'''
        pass  # pragma: no cover

    #
    #  RX - QUEUE
    #
    @abstractmethod
    def rx_get(self, size: int = None) -> bytearray:
        '''removes size numbers of bytes and return them'''
        pass  # pragma: no cover

    @abstractmethod
    def rx_peek(self, size: int = None) -> bytearray:
        '''returns size numbers of byte without removing them'''
        pass  # pragma: no cover

    @abstractmethod
    def rx_log(self, level, info):
        ''' logs the receive queue'''
        pass  # pragma: no cover

    @abstractmethod
    def rx_clear(self):
        ''' clear receive queue'''
        pass  # pragma: no cover

    @abstractmethod
    def rx_len(self):
        ''' get numner of bytes in the receive queue'''
        pass  # pragma: no cover

    @abstractmethod
    def rx_set_cb(self, callback):
        pass  # pragma: no cover

    #
    #  Protocol Callbacks
    #
    @abstractmethod
    def prot_set_timeout_cb(self, callback):
        pass  # pragma: no cover
