import logging
from dataclasses import dataclass, field
from typing import Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ceda_download_tool.auth import Auth

logger = logging.getLogger(__name__)


@dataclass
class SessionConfig:
    timeout: int = 30
    max_retries: int = 3
    backoff_factor: float = 0.5
    retry_statuses: tuple[int, ...] = field(default_factory=lambda: (429, 500, 502, 503, 504))

    def __post_init__(self):
        if self.timeout <= 0:
            raise ValueError("timeout must be positive")
        if self.max_retries < 0:
            raise ValueError("max retries cannot be negative")
        if self.backoff_factor < 0:
            raise ValueError("backoff factor cannot be negative")


class SessionManager:
    """
    manages http sessions with retry logic and authentication.

    example:
        auth = TokenAuth(token="your_token")              # with token authentication
        manager = SessionManager(auth=auth)
        session = manager.session

        config = SessionConfig(timeout=60, max_retries=5) # custom configuration
        manager = SessionManager(auth=auth, config=config)
    """

    def __init__(self, auth: Optional[Auth] = None, config: Optional[SessionConfig] = None):
        self._config = config or SessionConfig()
        self._auth = auth
        self._session = self._create_session()

        logger.info(f"SessionManager initialized (timeout={self._config.timeout}s, retries={self._config.max_retries})")

    def _create_session(self) -> requests.Session:
        session = requests.Session()

        # configure retry strategy
        retry_strategy = Retry(
            total=self._config.max_retries,
            backoff_factor=self._config.backoff_factor,
            status_forcelist=list(self._config.retry_statuses),
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)

        # apply authentication headers if provided
        if self._auth:
            session.headers.update(self._auth.headers())
            logger.debug("authentication headers applied to session")

        # wrap request method to apply default timeout
        original_request = session.request

        def request_with_timeout(*args, **kwargs):
            kwargs.setdefault("timeout", self._config.timeout)
            return original_request(*args, **kwargs)

        session.request = request_with_timeout

        return session

    @property
    def session(self) -> requests.Session:
        return self._session

    @property
    def config(self) -> SessionConfig:
        return self._config

    def update_auth(self, auth: Auth) -> None:
        self._auth = auth
        self._session.headers.update(auth.headers())
        logger.info("session authentication updated")


def create_session(timeout: int = 30, auth: Optional[Auth] = None, max_retries: int = 3) -> requests.Session:
    """
    create a configured requests session (convenience function).

    Args:
        timeout: request timeout in seconds.
        auth: optional token authentication.
        max_retries: maximum retry attempts.

    Returns:
        configured requests.Session instance.
    """
    config = SessionConfig(timeout=timeout, max_retries=max_retries)
    manager = SessionManager(auth=auth, config=config)
    return manager.session
