

class IterRegistry(type):
    def __iter__(cls):
        for ref in cls._registry:
            obj = ref()
            if obj is not None:
                yield obj
