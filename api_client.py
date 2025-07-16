"""
API Client for Ashescodex.com with rate limiting and caching support.
Handles pagination and robust error recovery.
"""

import asyncio
import aiohttp
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class APIResponse:
    """Structured response from API calls"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    status_code: Optional[int] = None
    page: Optional[int] = None
    total_pages: Optional[int] = None

class AshesCodexAPIClient:
    """
    Async API client for Ashescodex.com with rate limiting and caching.
    Respects server limitations and provides robust error handling.
    """
    
    def __init__(self, base_url: str = "https://api.ashescodex.com", 
                 rate_limit: float = 1.5, cache_dir: str = "cache"):
        self.base_url = base_url
        self.rate_limit = rate_limit  # seconds between requests (increased from 1.0)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.last_request_time = 0
        
        # Session will be created when needed
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Track request statistics
        self.stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'api_errors': 0,
            'rate_limit_delays': 0,
            'timeouts': 0,
            'retries': 0
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        # Reduced timeout and added connection limits
        timeout = aiohttp.ClientTimeout(
            total=15,      # Reduced from 30 seconds
            connect=5,     # Connection timeout
            sock_read=10   # Socket read timeout
        )
        
        connector = aiohttp.TCPConnector(
            limit=10,           # Maximum number of connections
            limit_per_host=5,   # Maximum connections per host
            keepalive_timeout=30
        )
        
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            headers={
                'User-Agent': 'AshesArtisanToolbox/1.0 (Personal Guild Tool)',
                'Accept': 'application/json',
                'Connection': 'keep-alive'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def _rate_limit_delay(self):
        """Implement rate limiting to be respectful to the API server"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit:
            delay = self.rate_limit - time_since_last
            logger.info(f"Rate limiting: waiting {delay:.2f} seconds")
            await asyncio.sleep(delay)
            self.stats['rate_limit_delays'] += 1
        
        self.last_request_time = time.time()
    
    def _get_cache_path(self, endpoint: str, params: Dict = None) -> Path:
        """Generate cache file path for given endpoint and parameters"""
        cache_key = endpoint.replace('/', '_')
        if params:
            param_str = '_'.join(f"{k}={v}" for k, v in sorted(params.items()))
            cache_key += f"_{param_str}"
        return self.cache_dir / f"{cache_key}.json"
    
    def _load_from_cache(self, cache_path: Path, max_age_hours: int = 24) -> Optional[Dict]:
        """Load data from cache if it exists and is not too old"""
        try:
            if not cache_path.exists():
                return None
            
            # Check if cache is too old
            cache_age = time.time() - cache_path.stat().st_mtime
            if cache_age > max_age_hours * 3600:
                logger.info(f"Cache expired for {cache_path.name}")
                return None
            
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.stats['cache_hits'] += 1
                logger.info(f"Cache hit for {cache_path.name}")
                return data
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load cache {cache_path}: {e}")
            return None
    
    def _save_to_cache(self, cache_path: Path, data: Dict):
        """Save data to cache file"""
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Cached data to {cache_path.name}")
        except IOError as e:
            logger.warning(f"Failed to save cache {cache_path}: {e}")
    
    async def _make_request(self, endpoint: str, params: Dict = None, 
                          max_retries: int = 3) -> APIResponse:
        """Make HTTP request with improved error handling and retries"""
        if not self.session:
            raise RuntimeError("API client not initialized. Use async context manager.")
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        for attempt in range(max_retries + 1):
            try:
                await self._rate_limit_delay()
                self.stats['total_requests'] += 1
                
                if attempt > 0:
                    self.stats['retries'] += 1
                    # Exponential backoff for retries
                    retry_delay = min(2 ** attempt, 10)
                    logger.info(f"Retry attempt {attempt}, waiting {retry_delay}s...")
                    await asyncio.sleep(retry_delay)
                
                async with self.session.get(url, params=params or {}) as response:
                    logger.info(f"API request: {url} - Status: {response.status} (attempt {attempt + 1})")
                    
                    if response.status == 200:
                        data = await response.json()
                        return APIResponse(
                            success=True,
                            data=data,
                            status_code=response.status,
                            page=params.get('page') if params else None
                        )
                    elif response.status == 429:
                        # Rate limited - wait longer before retry
                        logger.warning("Rate limited by server, waiting 10 seconds...")
                        await asyncio.sleep(10)
                        continue  # Retry
                    elif response.status in [502, 503, 504]:
                        # Server errors - retry
                        logger.warning(f"Server error {response.status}, will retry...")
                        continue
                    else:
                        # Client error - don't retry
                        error_text = await response.text()
                        self.stats['api_errors'] += 1
                        return APIResponse(
                            success=False,
                            error=f"HTTP {response.status}: {error_text}",
                            status_code=response.status
                        )
            
            except asyncio.TimeoutError:
                self.stats['timeouts'] += 1
                logger.warning(f"Request timeout (attempt {attempt + 1})")
                if attempt == max_retries:
                    return APIResponse(success=False, error="Request timeout after retries")
                continue  # Retry
                
            except aiohttp.ClientError as e:
                self.stats['api_errors'] += 1
                logger.warning(f"Network error: {str(e)} (attempt {attempt + 1})")
                if attempt == max_retries:
                    return APIResponse(success=False, error=f"Network error: {str(e)}")
                continue  # Retry
                
            except Exception as e:
                self.stats['api_errors'] += 1
                logger.error(f"Unexpected error: {str(e)}")
                return APIResponse(success=False, error=f"Unexpected error: {str(e)}")
        
        # Should not reach here
        return APIResponse(success=False, error="Max retries exceeded")
    
    async def get_items_page(self, page: int = 1, use_cache: bool = True) -> APIResponse:
        """Get a single page of items from the API"""
        endpoint = "items"
        params = {"page": page}
        
        # Check cache first
        if use_cache:
            cache_path = self._get_cache_path(endpoint, params)
            cached_data = self._load_from_cache(cache_path)
            if cached_data:
                return APIResponse(
                    success=True,
                    data=cached_data,
                    page=page
                )
        
        # Make API request
        response = await self._make_request(endpoint, params)
        
        # Cache successful responses
        if response.success and response.data:
            cache_path = self._get_cache_path(endpoint, params)
            self._save_to_cache(cache_path, response.data)
        
        return response
    
    async def get_items_batch(self, start_page: int = 1, batch_size: int = 10, 
                            use_cache: bool = True) -> Tuple[List[Dict], bool, int]:
        """
        Fetch a small batch of pages to reduce timeout risk.
        Returns (items, has_more_pages, last_page_fetched)
        """
        all_items = []
        current_page = start_page
        end_page = start_page + batch_size - 1
        consecutive_errors = 0
        max_consecutive_errors = 3
        
        logger.info(f"Fetching batch: pages {start_page} to {end_page}")
        
        while current_page <= end_page:
            try:
                response = await self.get_items_page(current_page, use_cache)
                
                if response.success and response.data:
                    consecutive_errors = 0
                    
                    items = response.data.get('data', [])
                    if not items:
                        logger.info(f"No items on page {current_page}, ending batch")
                        return all_items, False, current_page - 1
                    
                    all_items.extend(items)
                    logger.info(f"Batch progress: page {current_page}, {len(items)} items")
                    
                    # Check if we've reached the actual last page
                    current_page_num = response.data.get('current_page', current_page)
                    last_page = response.data.get('last_page', current_page)
                    
                    if current_page_num >= last_page:
                        logger.info(f"Reached API last page ({last_page}) in batch")
                        return all_items, False, current_page
                    
                    current_page += 1
                
                else:
                    consecutive_errors += 1
                    logger.warning(f"Failed to fetch page {current_page}: {response.error}")
                    
                    if consecutive_errors >= max_consecutive_errors:
                        logger.error(f"Too many errors in batch, stopping at page {current_page - 1}")
                        break
                    
                    # Short wait before retry
                    await asyncio.sleep(1)
            
            except Exception as e:
                consecutive_errors += 1
                logger.error(f"Batch error on page {current_page}: {e}")
                
                if consecutive_errors >= max_consecutive_errors:
                    break
                
                await asyncio.sleep(1)
        
        # Determine if there are more pages
        has_more = current_page <= end_page and consecutive_errors < max_consecutive_errors
        
        logger.info(f"Batch complete: {len(all_items)} items, has_more: {has_more}")
        return all_items, has_more, current_page - 1

    async def get_all_items(self, use_cache: bool = True, 
                          max_pages: int = 200, batch_size: int = 10) -> List[Dict]:
        """
        Fetch all items using smaller batches to reduce timeout risk.
        Processes in batches of pages with progress reporting.
        """
        all_items = []
        current_page = 1
        total_fetched = 0
        
        logger.info(f"Starting batch-based item fetch (batch size: {batch_size} pages)")
        
        while current_page <= max_pages:
            try:
                # Fetch a batch of pages
                batch_items, has_more, last_page = await self.get_items_batch(
                    current_page, batch_size, use_cache
                )
                
                if not batch_items:
                    logger.info("No items in batch, ending fetch")
                    break
                
                all_items.extend(batch_items)
                total_fetched += len(batch_items)
                
                logger.info(f"Progress: {total_fetched} total items from {last_page} pages")
                
                if not has_more:
                    logger.info("API indicates no more pages available")
                    break
                
                # Move to next batch
                current_page = last_page + 1
                
                # Small pause between batches to be extra respectful
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Batch fetch failed at page {current_page}: {e}")
                break
        
        logger.info(f"Finished batch fetch: {len(all_items)} total items")
        return all_items
    
    def get_stats(self) -> Dict:
        """Get request statistics"""
        return self.stats.copy()
    
    def clear_cache(self):
        """Clear all cached data"""
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                cache_file.unlink()
                logger.info(f"Deleted cache file: {cache_file.name}")
            except OSError as e:
                logger.warning(f"Failed to delete cache file {cache_file}: {e}")


# Example usage and testing
async def main():
    """Example usage of the API client"""
    async with AshesCodexAPIClient() as client:
        # Test single page
        response = await client.get_items_page(1)
        if response.success:
            print(f"First page contains {len(response.data.get('data', []))} items")
        
        # Test fetching all items (limited for testing)
        all_items = await client.get_all_items(max_pages=3)
        print(f"Total items fetched: {len(all_items)}")
        
        # Print statistics
        stats = client.get_stats()
        print(f"API Statistics: {stats}")


if __name__ == "__main__":
    asyncio.run(main())