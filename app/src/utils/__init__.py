import mimetypes
from importlib import import_module
from pathlib import Path
from collections.abc import Callable


class SourceFileLoader:
    """ Represents a SouceFileLoader (__loader__)"""
    name: str
    get_resource_reader: Callable


def load_modules(loader: SourceFileLoader):
    """Load the entire modules from a SourceFileLoader (__loader__)"""
    pkg = loader.name
    for load in loader.get_resource_reader().contents():

        if "python" not in str(mimetypes.guess_type(load)[0]):
            continue

        mod = Path(load).stem
        if mod == "__init__":
            continue

        import_module(pkg + "." + mod, pkg)
