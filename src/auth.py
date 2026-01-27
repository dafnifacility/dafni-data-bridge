import logging
import os
import re
from base64 import b64encode
from dataclasses import dataclass

import requests

from exceptions import AuthError, TokenValidationError

TOKEN_CREATE_URL = os.environ.get("TOKEN_CREATE_URL", "https://services.ceda.ac.uk/api/token/create/")
JWT_PATTERN = re.compile(os.environ.get("JWT_PATTERN", r"^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$"))

logger = logging.getLogger(__name__)


@dataclass
class TokenInfo:
    access_token: str
    token_type: str = "Bearer"

    def __post_init__(self):
        if not self.access_token:
            raise TokenValidationError("access token cannot be empty")


class Auth:
    """
    Example:
        auth = Auth(token="your_access_token")               # with existing token
        auth = Auth.from_credentials("username", "password") # generate new token
    """

    def __init__(self, token: str):
        """
        initialize with an existing access token

        Args:
            token: a valid jwt ceda access token

        Raises:
            TokenValidationError: if token is empty or invalid format.
        """
        self._validate_token(token)
        self._token_info = TokenInfo(access_token=token)
        logger.info("Auth initialized with provided token")

    @classmethod
    def from_credentials(cls, username: str, password: str, timeout: int = 30) -> "Auth":
        """
        generate a new access token from ceda credentials.

        Args:
            username: ceda account username.
            password: ceda account password.
            timeout: request timeout in seconds.

        Returns:
            TokenAuth instance with the generated token.

        Raises:
            AuthError: if token generation fails.
            TokenValidationError: if credentials are invalid.
        """
        cls._validate_credentials(username, password)

        logger.info(f"generating access token for user: {username}")

        # Create Basic auth header
        credentials = f"{username}:{password}"
        encoded = b64encode(credentials.encode("utf-8")).decode("ascii")
        headers = {"Authorization": f"Basic {encoded}"}

        try:
            response = requests.post(TOKEN_CREATE_URL, headers=headers, timeout=timeout)
        except requests.RequestException as e:
            logger.error(f"token request failed: {e}")
            raise AuthError(f"failed to connect to token service: {e}") from e

        if response.status_code == 401:
            logger.error("authentication failed: invalid credentials")
            raise AuthError("invalid username or password")

        if response.status_code != 200:
            logger.error(f"token generation failed with status {response.status_code}")
            raise AuthError(f"token generation failed: HTTP {response.status_code} - {response.text}")

        try:
            data = response.json()
            access_token = data["access_token"]
        except (ValueError, KeyError) as e:
            logger.error(f"failed to parse token response: {e}")
            raise AuthError("invalid response from token service") from e

        logger.info("access token generated successfully")
        return cls(token=access_token)

    @staticmethod
    def _validate_token(token: str) -> None:
        if not isinstance(token, str):
            raise TokenValidationError("token must be a string")

        stripped = token.strip()
        if not stripped:
            raise TokenValidationError("token cannot be empty or whitespace only")

        # check jwt format (3 base64url parts separated by dots)
        if not JWT_PATTERN.match(stripped):
            logger.warning("token does not match expected jwt format")

    @staticmethod
    def _validate_credentials(username: str, password: str) -> None:
        if not username or not isinstance(username, str):
            raise TokenValidationError("username must be a non-empty string")

        if not password or not isinstance(password, str):
            raise TokenValidationError("password must be a non-empty string")

        if username.strip() != username:
            logger.warning("username has leading/trailing whitespace")

    @property
    def token(self) -> str:
        return self._token_info.access_token

    def headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token_info.access_token}",
        }

    def __repr__(self) -> str:
        # only show first/last few chars of token for security
        token = self._token_info.access_token
        masked = f"{token[:8]}...{token[-8:]}" if len(token) > 20 else "***"
        return f"TokenAuth(token='{masked}')"
