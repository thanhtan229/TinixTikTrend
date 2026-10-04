class AppException(Exception):
    """Base exception for all application errors."""
    def __init__(self, message: str, detail: str = None):
        self.message = message
        self.detail = detail
        super().__init__(self.message)


class ResourceNotFoundException(AppException):
    """Raised when a requested resource is not found."""
    pass


class CollectorException(AppException):
    """Raised when a collector fails during crawling or retrieval."""
    pass


class ParserException(AppException):
    """Raised when parsing TikTok HTML or JSON response fails."""
    pass


class RateLimitException(CollectorException):
    """Raised when TikTok rate limits requests."""
    pass


class CrawlerActiveException(AppException):
    """Raised when attempting to start a crawl while one is already running."""
    pass
