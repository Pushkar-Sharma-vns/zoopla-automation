import asyncio
import random
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SecurityManager:
    """
    Security utilities to ensure respectful and human-like automation
    Prevents rate limiting and maintains ethical browsing patterns
    """
    
    def __init__(self):
        self.last_request_time: Optional[datetime] = None
        self.request_count = 0
        self.session_start = datetime.now()
        
    async def smart_delay(self, min_seconds: float = 2.0, max_seconds: float = 5.0) -> None:
        """Random delay to mimic human behavior"""
        delay = random.uniform(min_seconds, max_seconds)
        logger.debug(f"Smart delay: {delay:.2f} seconds")
        await asyncio.sleep(delay)
        
    async def scroll_delay(self) -> None:
        """Human-like scrolling delay"""
        delay = random.uniform(3.0, 6.0)
        logger.debug(f"Scroll delay: {delay:.2f} seconds")
        await asyncio.sleep(delay)
        
    async def click_delay(self) -> None:
        """Human-like clicking delay"""
        delay = random.uniform(1.0, 3.0)
        logger.debug(f"Click delay: {delay:.2f} seconds")
        await asyncio.sleep(delay)
        
    async def page_load_wait(self) -> None:
        """Wait for page to fully load like a human would"""
        delay = random.uniform(5.0, 8.0)
        logger.debug(f"Page load wait: {delay:.2f} seconds")
        await asyncio.sleep(delay)
        
    async def city_search_throttle(self) -> None:
        """Throttle city searches to max 1 per 10-15 seconds"""
        if self.last_request_time:
            time_since_last = datetime.now() - self.last_request_time
            min_interval = timedelta(seconds=random.uniform(10, 15))
            
            if time_since_last < min_interval:
                wait_time = (min_interval - time_since_last).total_seconds()
                logger.info(f"Throttling city search: waiting {wait_time:.1f} seconds")
                await asyncio.sleep(wait_time)
                
        self.last_request_time = datetime.now()
        self.request_count += 1
        
    async def respectful_backoff(self, attempt: int) -> None:
        """Exponential backoff with randomization for errors"""
        base_delay = 2 ** attempt  # 2, 4, 8, 16 seconds
        jitter = random.uniform(0.5, 1.5)  # Add randomness
        delay = base_delay * jitter
        
        logger.warning(f"Respectful backoff (attempt {attempt}): {delay:.1f} seconds")
        await asyncio.sleep(delay)
        
    async def handle_blocking_scenario(self, page_content: str, page_title: str = "") -> bool:
        """Handle common blocking scenarios with improved detection"""
        
        # Skip blocking detection if we have a successful Zoopla page title
        if page_title and ("zoopla" in page_title.lower() and 
                          any(keyword in page_title.lower() for keyword in ["property", "search", "buy", "rent", "house"])):
            logger.debug("✅ Valid Zoopla page detected - skipping blocking check")
            return False
        
        # More specific blocking indicators (avoiding false positives)
        critical_blocking_indicators = [
            "access denied", "blocked", "captcha required", 
            "verify you are human", "rate limit exceeded", 
            "too many requests", "suspicious activity detected",
            "bot detection enabled", "automated requests blocked"
        ]
        
        # Check for actual blocking page indicators (more specific)
        content_lower = page_content.lower()
        
        # Look for specific blocking patterns rather than general words
        blocking_patterns = [
            "you have been blocked",
            "access to this page has been denied", 
            "please complete the captcha",
            "rate limit has been exceeded",
            "too many requests from your ip",
            "automated requests are not allowed"
        ]
        
        # Check both individual indicators and specific patterns
        is_blocked = (
            any(indicator in content_lower for indicator in critical_blocking_indicators) or
            any(pattern in content_lower for pattern in blocking_patterns)
        )
        
        # Additional check: if page is very short, might be a blocking page
        if len(page_content.strip()) < 200 and any(word in content_lower for word in ["blocked", "denied", "captcha"]):
            is_blocked = True
        
        if is_blocked:
            logger.warning("🚨 Actual blocking scenario detected! Implementing recovery strategy...")
            logger.warning(f"Page title: '{page_title}'")
            logger.warning(f"Content length: {len(page_content)} chars")
            
            # Long delay before retry
            recovery_delay = random.uniform(30, 60)
            logger.warning(f"Recovery delay: {recovery_delay:.1f} seconds")
            await asyncio.sleep(recovery_delay)
            
            return True
            
        return False
        
    def get_session_stats(self) -> Dict[str, Any]:
        """Get current session statistics"""
        session_duration = datetime.now() - self.session_start
        
        return {
            "session_duration": str(session_duration),
            "request_count": self.request_count,
            "requests_per_minute": self.request_count / max(session_duration.total_seconds() / 60, 1),
            "last_request": str(self.last_request_time) if self.last_request_time else None
        }
        
    def is_session_healthy(self) -> bool:
        """Check if current session maintains healthy request patterns"""
        stats = self.get_session_stats()
        
        # Max 4 requests per minute to be conservative
        if stats["requests_per_minute"] > 4:
            logger.warning(f"Session unhealthy: {stats['requests_per_minute']:.1f} requests/min")
            return False
            
        return True

# Global security manager instance
security_manager = SecurityManager()

# Convenience functions for easy import
async def smart_delay(min_seconds: float = 2.0, max_seconds: float = 5.0) -> None:
    """Random delay between actions"""
    await security_manager.smart_delay(min_seconds, max_seconds)

async def scroll_delay() -> None:
    """Delay for scrolling actions"""
    await security_manager.scroll_delay()

async def click_delay() -> None:
    """Delay for clicking actions"""
    await security_manager.click_delay()

async def page_load_wait() -> None:
    """Wait for page loads"""
    await security_manager.page_load_wait()

async def city_search_throttle() -> None:
    """Throttle city searches"""
    await security_manager.city_search_throttle()

async def respectful_backoff(attempt: int) -> None:
    """Backoff on errors"""
    await security_manager.respectful_backoff(attempt)

async def handle_blocking_scenario(page_content: str) -> bool:
    """Handle blocking scenarios"""
    return await security_manager.handle_blocking_scenario(page_content)