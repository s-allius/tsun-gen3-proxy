from quart import Blueprint
from quart import request, session, redirect
from quart_babel import _


LANGUAGES = {
    'en': _('English'),
    'de': _('German'),
    'fr': _('French')
}

i18n_routes = Blueprint('i18n_routes', __name__)


def my_get_locale():
    try:
        language = session['language']
    except KeyError:
        language = None
    if language is not None:
        return language

    # check how to get the locale form for the add-on - hass.selectedLanguage
    # logging.info("get_locale(%s)", request.accept_languages)
    return request.accept_languages.best_match(LANGUAGES.keys())


@i18n_routes.route('/language/<language>')
def set_language(language=None):
    if language in LANGUAGES:
        session['language'] = language
    return redirect(request.referrer)
