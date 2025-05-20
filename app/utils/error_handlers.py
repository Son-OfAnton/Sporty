"""
Error handling utilities for the Sporty application.
"""

import logging
import sys
from typing import Dict, Any, Optional, Callable

logger = logging.getLogger(__name__)

class APIError(Exception):
    """Exception raised for API-related errors."""
    
    def __init__(self, message: str, response: Optional[Dict[str, Any]] = None):
        """
        Initialize the exception.
        
        Args:
            message: Error message
            response: API response that caused the error
        """
        self.message = message
        self.response = response
        super().__init__(self.message)
        
class AuthenticationError(APIError):
    """Exception raised for authentication errors."""
    pass
    
class RateLimitError(APIError):
    """Exception raised for rate limit exceeded errors."""
    pass
    
class NotFoundError(APIError):
    """Exception raised for resource not found errors."""
    pass
    
def handle_api_error(response: Dict[str, Any]) -> None:
    """
    Handle API errors based on the response.
    
    Args:
        response: API response
        
    Raises:
        AuthenticationError: For authentication errors
        RateLimitError: For rate limit exceeded errors
        NotFoundError: For resource not found errors
        APIError: For other API errors
    """
    errors = response.get("errors", {})
    
    if not errors:
        return
        
    # Check for specific error types
    error_msg = str(errors)
    
    if "token" in error_msg.lower() or "api key" in error_msg.lower() or "authentication" in error_msg.lower():
        raise AuthenticationError("Authentication error", response)
        
    if "rate limit" in error_msg.lower():
        raise RateLimitError("Rate limit exceeded", response)
        
    if "not found" in error_msg.lower():
        raise NotFoundError("Resource not found", response)
        
    # Generic API error
    raise APIError(f"API error: {error_msg}", response)
    
def setup_error_handling(exit_on_error: bool = False) -> None:
    """
    Set up global error handling.
    
    Args:
        exit_on_error: Whether to exit the program on uncaught exceptions
    """
    def exception_handler(exctype, value, traceback):
        """Custom exception handler."""
        logger.error("Uncaught exception", exc_info=(exctype, value, traceback))
        if exit_on_error:
            sys.exit(1)
            
    # Set the exception handler
    sys.excepthook = exception_handler
    
def create_error_callback(
    silent: bool = False,
    reraise: bool = True,
    custom_handler: Optional[Callable[[Dict[str, Any]], None]] = None
) -> Callable[[Dict[str, Any]], None]:
    """
    Create an error callback for API responses.
    
    Args:
        silent: Whether to suppress logging
        reraise: Whether to re-raise exceptions
        custom_handler: Custom error handler function
        
    Returns:
        Error callback function
    """
    def callback(response: Dict[str, Any]) -> None:
        try:
            if custom_handler:
                custom_handler(response)
            else:
                handle_api_error(response)
        except Exception as e:
            if not silent:
                logger.error(f"API error: {e}")
            if reraise:
                raise
                
    return callback