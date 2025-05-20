"""
Utilities for API response parsing and handling.
"""

import logging
from typing import Dict, Any, List, Optional, TypeVar, Callable, Union

logger = logging.getLogger(__name__)

# Generic type for parse results
T = TypeVar('T')

def parse_response(
    response: Dict[str, Any],
    data_key: str = "response",
    error_handler: Optional[Callable[[Dict[str, Any]], None]] = None
) -> List[Dict[str, Any]]:
    """
    Parse the standard API response format.
    
    Args:
        response: API response dictionary
        data_key: Key containing the actual data
        error_handler: Function to call if the response indicates an error
        
    Returns:
        List of data items from the response
        
    Raises:
        ValueError: If the response does not contain the expected structure
    """
    # Check for successful response
    if not response.get("results"):
        msg = f"API returned no results: {response.get('errors', {})}"
        logger.warning(msg)
        if error_handler:
            error_handler(response)
        return []
        
    # Extract the data
    if data_key not in response:
        msg = f"Response does not contain the expected key: {data_key}"
        logger.error(msg)
        raise ValueError(msg)
        
    return response[data_key]
    
def extract_entity(data: Dict[str, Any], entity_key: str) -> Dict[str, Any]:
    """
    Extract a specific entity from a data item.
    
    Args:
        data: Data item
        entity_key: Key of the entity to extract
        
    Returns:
        The extracted entity
        
    Raises:
        KeyError: If the entity key does not exist
    """
    if entity_key not in data:
        raise KeyError(f"Data does not contain the key: {entity_key}")
        
    return data[entity_key]
    
def ensure_list(data: Union[List[T], T]) -> List[T]:
    """
    Ensure that the data is a list.
    
    Args:
        data: Data to check
        
    Returns:
        Data as a list
    """
    if not isinstance(data, list):
        return [data]
    return data
    
def filter_data(
    data: List[Dict[str, Any]],
    filters: Dict[str, Any],
    match_all: bool = True
) -> List[Dict[str, Any]]:
    """
    Filter data based on key-value pairs.
    
    Args:
        data: List of data items to filter
        filters: Key-value pairs to filter by
        match_all: If True, all filters must match; if False, any filter can match
        
    Returns:
        Filtered data
    """
    if not filters:
        return data
        
    result = []
    
    for item in data:
        matches = 0
        for key, value in filters.items():
            if key in item and item[key] == value:
                matches += 1
                if not match_all:
                    # Any match is enough
                    result.append(item)
                    break
                    
        if match_all and matches == len(filters):
            # All filters matched
            result.append(item)
            
    return result