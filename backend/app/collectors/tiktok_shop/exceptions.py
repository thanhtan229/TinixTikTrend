from app.core.exceptions import AppException


class CollectorError(AppException):
    """Base exception for TikTok Shop collector operations."""
    pass


class ParseError(CollectorError):
    """Raised when extracting data from TikTok HTML/JSON fails."""
    pass


class BlockedError(CollectorError):
    """Raised when request is blocked (HTTP 403, 429, CAPTCHA)."""
    def __init__(self, message: str, reason: str = "security_check"):
        self.reason = reason
        super().__init__(message)


class BrowserInitError(CollectorError):
    """Raised when Playwright browser fails to initialize."""
    pass
