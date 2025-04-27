from quart import request, session, redirect, abort
from quart_babel import _
from quart_babel.locale import get_locale as babel_get_locale

from . import web

LANGUAGES = {
    'en': _('English'),
    'de': _('German'),
    'fr': _('French')
}


def get_locale():
    try:
        language = session['language']
    except KeyError:
        language = None
    if language is not None:
        return language

    # check how to get the locale form for the add-on - hass.selectedLanguage
    # logging.info("get_locale(%s)", request.accept_languages)
    return request.accept_languages.best_match(LANGUAGES.keys())


def get_tz():
    return 'CET'


@web.context_processor
def utility_processor():
    return dict(lang=babel_get_locale(),
                lang_str=LANGUAGES.get(str(babel_get_locale()), "English"),
                languages=LANGUAGES)


@web.route('/language/<language>')
def set_language(language=None):
    if language in LANGUAGES:
        session['language'] = language
        return redirect(request.referrer)
    return abort(400)
