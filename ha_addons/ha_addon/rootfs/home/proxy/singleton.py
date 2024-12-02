from weakref import WeakValueDictionary


class Singleton(type):
    _instances = WeakValueDictionary()

    def __call__(cls, *args, **kwargs):
        # logger_mqtt.debug('singleton: __call__')
        if cls not in cls._instances:
            instance = super(Singleton,
                             cls).__call__(*args, **kwargs)
            cls._instances[cls] = instance

        return cls._instances[cls]
