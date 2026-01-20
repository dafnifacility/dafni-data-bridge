import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session(timeout:int):
    session = requests.Session()

    retries = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
    )

    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)

    session.request = _with_timeout(session.request, timeout)
    return session

def _with_timeout(request, timeout):
    def wrapped(*args, **kwargs):
        kwargs.setdefault("timeout", timeout)
        return request(*args, **kwargs)
    return wrapped