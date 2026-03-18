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


class ValidationError(DownloadError):
    """raised when input validation fails."""

    pass


class BucketNotFoundError(DFTError):
    """raised when S3 Bucket is not found."""

    pass
