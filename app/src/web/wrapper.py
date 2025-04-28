from quart import url_for as quart_url_for
from . import web


def url_for(*args, **kwargs):
    """Return the url for a specific endpoint.

    This wrapper optionally convert into a relative url.

    This is most useful in templates and redirects to create a URL
    that can be used in the browser.

    Arguments:
        endpoint: The endpoint to build a url for, if prefixed with
            ``.`` it targets endpoint's in the current blueprint.
        _anchor: Additional anchor text to append (i.e. #text).
        _external: Return an absolute url for external (to app) usage.
        _method: The method to consider alongside the endpoint.
        _scheme: A specific scheme to use.
        values: The values to build into the URL, as specified in
            the endpoint rule.
    """
    url = quart_url_for(*args, **kwargs)
    print(f"wrapper url_for: {url}")
    if '/' == url[0] and web.build_relative_urls:
        url = '.' + url
    return url
