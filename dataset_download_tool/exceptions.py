class DFTError(Exception):
    """base exception for all dft (data federation tool)-related errors."""

    pass


class AuthError(DFTError):
    """raised when authentication fails."""

    pass


class TokenValidationError(AuthError):
    """raised when token validation fails."""

    pass


class DownloadError(DFTError):
    """raised when a download operation fails."""

    pass


class HTTPError(DownloadError):
    """raised when HTTP request fails."""

    def __init__(self, message: str, status_code: int = None, url: str = None):
        super().__init__(message)
        self.status_code = status_code
        self.url = url


class AuthenticationRequiredError(HTTPError):
    """raised when authentication is required but not provided."""

    pass


class ValidationError(DownloadError):
    """raised when input validation fails."""

    pass


class BucketNotFoundError(DFTError):
    """raised when S3 Bucket is not found."""

    pass
