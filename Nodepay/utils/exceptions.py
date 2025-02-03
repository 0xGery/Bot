class SentinelException(Exception):
    """Base exception for all Sentinel errors"""
    pass

class ProxyError(SentinelException):
    """Raised when there's an issue with proxy configuration or connection"""
    pass

class AuthenticationError(SentinelException):
    """Raised when authentication fails"""
    pass

class RateLimitError(SentinelException):
    """Raised when rate limit is exceeded"""
    pass

class NetworkError(SentinelException):
    """Raised when network-related issues occur"""
    pass
