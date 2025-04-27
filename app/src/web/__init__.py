'''Quart blueprint for the proxy webserver with the dashboard

Usage:
    app = Quart(__name__, ...)
    Web(app)
'''
from quart import Quart, Blueprint
from quart_babel import Babel
from utils import load_modules

web = Blueprint('web', __name__)

load_modules(__loader__)


class Web:
    '''Helper Class to register the Blueprint at Quart and
    initializing Babel'''
    def __init__(self, app: Quart, translation_directories: str | list[str]):
        app.register_blueprint(web)

        from .i18n import get_locale, get_tz
        global babel
        babel = Babel(
            app,
            locale_selector=get_locale,
            timezone_selector=get_tz,
            default_translation_directories=translation_directories)
