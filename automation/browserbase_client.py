import asyncio
import logging
import os
import json
import random
from datetime import datetime
from typing import Dict, Any, Optional, List
from stagehand import Stagehand, StagehandConfig
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from config.settings import settings
from utils.security_utils import smart_delay, respectful_backoff, handle_blocking_scenario

logger = logging.getLogger(__name__)

class BrowserbaseClient:
    def __init__(self, enable_recording: bool = True):
        # Build config parameters, excluding empty values
        config_params = {
            "env": "BROWSERBASE",
            "api_key": settings.BROWSERBASE_API_KEY,
            "project_id": settings.BROWSERBASE_PROJECT_ID,
            "model_name": settings.MODEL_NAME,
            "model_api_key": settings.MODEL_API_KEY,
        }
        
        # Only add api_url if STAGEHAND_API_URL is properly set with protocol
        if settings.STAGEHAND_API_URL and settings.STAGEHAND_API_URL.strip() and (
            settings.STAGEHAND_API_URL.startswith('http://') or 
            settings.STAGEHAND_API_URL.startswith('https://')
        ):
            config_params["api_url"] = settings.STAGEHAND_API_URL
        
        # Validate required parameters
        required_params = ["api_key", "project_id", "model_api_key"]
        for param in required_params:
            if not config_params.get(param):
                raise ValueError(f"Missing required parameter: {param}")
        
        logger.info(f"Creating StagehandConfig with params: {list(config_params.keys())}")
        logger.debug(f"API Key: {config_params['api_key'][:20]}...")
        logger.debug(f"Project ID: {config_params['project_id']}")
        logger.debug(f"Model: {config_params['model_name']}")
        
        self.config = StagehandConfig(**config_params)
        self.stagehand: Optional[Stagehand] = None
        self.enable_recording = enable_recording
        self.screenshot_counter = 0
        self.session_id: Optional[str] = None
        
        # Anti-detection configuration
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/120.0"
        ]
        
        # Cloudflare bypass cookies (legitimate session cookies)
        import time
        current_timestamp = int(time.time())
        
        self.cloudflare_cookies = [
            # Main Cloudflare clearance cookie - this is key for bypass
            {"name": "cf_clearance", "value": f"cf_{random.randint(10000000, 99999999)}_{current_timestamp}", "domain": ".zoopla.co.uk"},
            
            # Cloudflare challenge completion tokens
            {"name": "__cf_bm", "value": f"cf_bm_{random.randint(100000000000, 999999999999)}_{current_timestamp}", "domain": ".zoopla.co.uk"},
            {"name": "_cfuvid", "value": f"cfuvid_{random.randint(100000000, 999999999)}_{current_timestamp}", "domain": ".zoopla.co.uk"},
            
            # Browser validation cookies
            {"name": "__cflb", "value": f"cflb_{random.randint(1000000, 9999999)}", "domain": ".zoopla.co.uk"},
            {"name": "_cf_challenge", "value": "passed", "domain": ".zoopla.co.uk"},
            
            # Session persistence cookies
            {"name": "cf_ob_info", "value": f"cf_ob_{current_timestamp}_{random.randint(1000, 9999)}", "domain": ".zoopla.co.uk"},
            {"name": "cf_use_ob", "value": "0", "domain": ".zoopla.co.uk"},
        ]
        
        # Zoopla-specific cookies (in addition to Cloudflare)
        self.zoopla_cookies = [
            {"name": "zpg_suid", "value": f"zuid_{random.randint(100000, 999999)}", "domain": ".zoopla.co.uk"},
            {"name": "_ga", "value": f"GA1.2.{random.randint(100000000, 999999999)}.{random.randint(1600000000, 1700000000)}", "domain": ".zoopla.co.uk"},
            {"name": "_gid", "value": f"GA1.2.{random.randint(100000000, 999999999)}", "domain": ".zoopla.co.uk"},
            {"name": "session_id", "value": f"sess_{random.randint(1000000, 9999999)}", "domain": ".zoopla.co.uk"},
            {"name": "zpg_viewedproperties", "value": "", "domain": ".zoopla.co.uk"},
            {"name": "ab_test_bucket", "value": f"bucket_{random.choice(['A', 'B', 'C'])}", "domain": ".zoopla.co.uk"},
            {"name": "zpg_cohort_2018", "value": f"cohort_{random.choice(['control', 'test_a', 'test_b'])}", "domain": ".zoopla.co.uk"},
            {"name": "zpg_gdpr_consent", "value": "1", "domain": ".zoopla.co.uk"},
        ]
        
    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
        
    async def initialize(self) -> None:
        """Initialize the Stagehand client with session recording"""
        try:
            self.stagehand = Stagehand(self.config)
            await self.stagehand.init()
            # import pdb; pdb.set_trace()
            # Get session ID from the stagehand instance
            self.session_id = getattr(self.stagehand, 'session_id', None)
            
            # Configure viewport for consistent screenshots
            page = self.stagehand.page
            await page.set_viewport_size({
                "width": settings.VIDEO_WIDTH,
                "height": settings.VIDEO_HEIGHT
            })
            
            # Setup anti-detection measures
            await self._setup_anti_detection()
            
            logger.info(f"Browserbase client initialized successfully. Session ID: {self.session_id}")
            if self.session_id and self.stagehand.env == "BROWSERBASE":
                logger.info(f"Browser session: https://www.browserbase.com/sessions/{self.session_id}")
            logger.info(f"Screenshot recording enabled: {self.enable_recording}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Browserbase client: {e}")
            raise
            
    async def close(self) -> None:
        """Close the Stagehand client"""
        if self.stagehand:
            try:
                await self.stagehand.close()
                logger.info("Browserbase client closed successfully")
            except Exception as e:
                logger.error(f"Error closing Browserbase client: {e}")
            finally:
                self.stagehand = None
                self.session_id = None
                
    async def _setup_anti_detection(self) -> None:
        """Setup anti-detection measures including cookies, user agents, and browser properties"""
        try:
            page = self.stagehand.page
            
            # 1. Set random user agent
            user_agent = random.choice(self.user_agents)
            await page.set_extra_http_headers({"User-Agent": user_agent})
            logger.info(f"Set user agent: {user_agent[:50]}...")
            
            # 2. Add randomized viewport with small variations
            viewport_width = settings.VIDEO_WIDTH + random.randint(-50, 50)
            viewport_height = settings.VIDEO_HEIGHT + random.randint(-30, 30)
            await page.set_viewport_size({
                "width": max(1200, viewport_width),
                "height": max(680, viewport_height)
            })
            logger.info(f"Randomized viewport: {viewport_width}x{viewport_height}")
            
            # 3. Set up legitimate Zoopla cookies to bypass blocking
            await self._setup_zoopla_cookies()
            
            # 4. Set additional headers to mimic real browser
            await page.set_extra_http_headers({
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-GB,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Cache-Control": "max-age=0"
            })
            
            # 5. Add realistic browser properties
            await page.add_init_script("""
                // Remove webdriver property
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                
                // Mock plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                
                // Mock languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en'],
                });
                
                // Mock permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
            """)
            
            logger.info("✅ Anti-detection measures configured successfully")
            
        except Exception as e:
            logger.warning(f"Failed to setup anti-detection measures: {e}")
            # Don't raise - continue with basic setup
            
    async def _setup_zoopla_cookies(self) -> None:
        """Set up Cloudflare and Zoopla-specific cookies to bypass blocking"""
        try:
            page = self.stagehand.page
            context = page.context
            
            # First, add Cloudflare bypass cookies (these are critical)
            for cookie in self.cloudflare_cookies:
                await context.add_cookies([{
                    "name": cookie["name"],
                    "value": cookie["value"],
                    "domain": cookie["domain"],
                    "path": "/",
                    "httpOnly": False,
                    "secure": True,
                    "sameSite": "None"  # Important for Cloudflare cookies
                }])
            
            # Then add Zoopla-specific cookies
            for cookie in self.zoopla_cookies:
                await context.add_cookies([{
                    "name": cookie["name"],
                    "value": cookie["value"],
                    "domain": cookie["domain"],
                    "path": "/",
                    "httpOnly": False,
                    "secure": True,
                    "sameSite": "Lax"
                }])
                
            total_cookies = len(self.cloudflare_cookies) + len(self.zoopla_cookies)
            logger.info(f"Added {len(self.cloudflare_cookies)} Cloudflare + {len(self.zoopla_cookies)} Zoopla = {total_cookies} bypass cookies")
            
        except Exception as e:
            logger.warning(f"Failed to setup cookies: {e}")
            
    async def simulate_human_browsing(self) -> None:
        """Simulate human browsing behavior before accessing Zoopla"""
        try:
            logger.info("🤖 Simulating human browsing behavior...")
            
            # Visit a neutral site first to establish browsing history
            await self.stagehand.page.goto("https://www.google.com")
            await smart_delay(2.0, 4.0)
            
            # Simulate some mouse movements and scrolling
            await self.stagehand.page.mouse.move(random.randint(100, 500), random.randint(100, 400))
            await smart_delay(1.0, 2.0)
            await self.stagehand.page.mouse.wheel(0, random.randint(100, 300))
            await smart_delay(1.0, 2.0)
            
            # Visit one more site to create realistic referrer
            await self.stagehand.page.goto("https://www.rightmove.co.uk")
            await smart_delay(2.0, 3.0)
            
            logger.info("✅ Human browsing simulation completed")
            
        except Exception as e:
            logger.warning(f"Human browsing simulation failed: {e}")
            # Don't raise - continue with main flow
            
    async def _handle_cloudflare_challenge(self) -> bool:
        """Handle Cloudflare challenge by waiting for natural completion"""
        try:
            logger.info("⏳ Detecting and handling Cloudflare challenge...")
            
            page = self.stagehand.page
            max_attempts = 24  # 2 minutes total (24 * 5 seconds)
            
            for attempt in range(max_attempts):
                await asyncio.sleep(5)
                
                title = await page.title()
                logger.info(f"Challenge check {attempt + 1}/{max_attempts}: '{title}'")
                
                # Check if Cloudflare challenge is completed
                if "just a moment" not in title.lower() and "cloudflare" not in title.lower():
                    if "zoopla" in title.lower() or "property" in title.lower() or len(title) > 10:
                        logger.info("✅ Cloudflare challenge completed successfully!")
                        
                        # Brief wait for full page load (skip networkidle to avoid timeout)
                        await smart_delay(3.0, 5.0)
                        try:
                            await page.wait_for_load_state("networkidle", timeout=10000)
                        except Exception:
                            logger.info("Page load timeout ignored - Cloudflare challenge completed")
                        return True
                
                # Simulate human-like behavior during wait
                if attempt % 4 == 0:  # Every 20 seconds
                    try:
                        viewport = await page.evaluate("() => ({ width: window.innerWidth, height: window.innerHeight })")
                        await page.mouse.move(
                            viewport["width"] // 2 + (attempt % 100) - 50,
                            viewport["height"] // 2 + (attempt % 80) - 40
                        )
                        logger.info("🖱️ Simulated human interaction during challenge")
                    except Exception:
                        pass
            
            logger.warning("⚠️ Cloudflare challenge did not complete within timeout")
            return False
            
        except Exception as e:
            logger.error(f"Error handling Cloudflare challenge: {e}")
            return False
                
    async def navigate_to_url(self, url: str) -> None:
        """Navigate to a specific URL with security measures and retry logic"""
        if not self.stagehand:
            raise RuntimeError("Stagehand client not initialized")
        
        # If navigating to Zoopla, simulate human browsing first
        is_zoopla = "zoopla.co.uk" in url.lower()
        if is_zoopla:
            await self.simulate_human_browsing()
        
        for attempt in range(settings.MAX_RETRIES):
            try:
                # Smart delay before navigation (longer for Zoopla)
                delay_min = 3.0 if is_zoopla else 1.0
                delay_max = 6.0 if is_zoopla else 3.0
                await smart_delay(delay_min, delay_max)
                
                # Enhanced navigation for Zoopla
                if is_zoopla:
                    # Add random referrer header
                    referrers = [
                        "https://www.google.co.uk/search?q=property+search",
                        "https://www.rightmove.co.uk/",
                        "https://www.google.com/",
                        "https://www.bing.com/search?q=london+properties"
                    ]
                    await self.stagehand.page.set_extra_http_headers({
                        "Referer": random.choice(referrers)
                    })
                
                await self.stagehand.page.goto(url, wait_until="domcontentloaded", timeout=60000)
                
                # For Zoopla, handle Cloudflare challenge naturally
                if is_zoopla:
                    await self._handle_cloudflare_challenge()
                else:
                    await smart_delay(2.0, 4.0)  # Let page settle
                    await self.stagehand.page.wait_for_load_state("networkidle", timeout=30000)
                
                # Check for blocking scenarios (with page title context)
                page_content = await self.stagehand.page.content()
                page_title = await self.stagehand.page.title()
                if await handle_blocking_scenario(page_content, page_title):
                    logger.warning(f"Blocking detected during navigation to {url}, retrying...")
                    continue
                
                logger.info(f"Successfully navigated to: {url}")
                return
                
            except Exception as e:
                logger.error(f"Failed to navigate to {url} (attempt {attempt + 1}): {e}")
                if attempt < settings.MAX_RETRIES - 1:
                    await respectful_backoff(attempt)
                else:
                    raise
            
    @retry(
        stop=stop_after_attempt(settings.MAX_RETRIES),
        wait=wait_exponential(multiplier=settings.RETRY_DELAY, min=1, max=10),
        retry=retry_if_exception_type((Exception,))
    )
    async def act(self, instruction: str) -> Dict[str, Any]:
        """Perform an action using Stagehand's act method"""
        if not self.stagehand:
            raise RuntimeError("Stagehand client not initialized")
            
        try:
            # Use the correct API - act method is on the page object
            result = await self.stagehand.page.act(instruction)
            logger.info(f"Action completed: {instruction}")
            return result
        except Exception as e:
            logger.error(f"Failed to perform action '{instruction}': {e}")
            raise
            
    @retry(
        stop=stop_after_attempt(settings.MAX_RETRIES),
        wait=wait_exponential(multiplier=settings.RETRY_DELAY, min=1, max=10),
        retry=retry_if_exception_type((Exception,))
    )
    async def extract_data(self, instruction: str, schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Extract data using Stagehand's extract method"""
        if not self.stagehand:
            raise RuntimeError("Stagehand client not initialized")
            
        try:
            # Use the correct API - extract method is on the page object
            if schema:
                result = await self.stagehand.page.extract(instruction, schema=schema)
            else:
                result = await self.stagehand.page.extract(instruction)
            logger.info(f"Data extracted successfully: {instruction}")
            return result
        except Exception as e:
            logger.error(f"Failed to extract data '{instruction}': {e}")
            raise
            
    @retry(
        stop=stop_after_attempt(settings.MAX_RETRIES),
        wait=wait_exponential(multiplier=settings.RETRY_DELAY, min=1, max=10),
        retry=retry_if_exception_type((Exception,))
    )
    async def observe(self, instruction: str) -> str:
        """Observe page content using Stagehand's observe method"""
        if not self.stagehand:
            raise RuntimeError("Stagehand client not initialized")
            
        try:
            result = await self.stagehand.observe(instruction)
            logger.info(f"Observation completed: {instruction}")
            return result
        except Exception as e:
            logger.error(f"Failed to observe '{instruction}': {e}")
            raise
            
    async def take_screenshot(self, file_path: str, full_page: bool = False) -> str:
        """Take a screenshot of the current page with timeout handling"""
        if not self.stagehand:
            raise RuntimeError("Stagehand client not initialized")
            
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Take screenshot with reduced timeout and fallback options
            try:
                await self.stagehand.page.screenshot(
                    path=file_path, 
                    full_page=full_page,
                    timeout=15000  # Reduced from default 30s to 15s
                )
            except Exception as screenshot_error:
                logger.warning(f"Screenshot with full options failed: {screenshot_error}")
                
                # Fallback: Try screenshot without full_page option
                try:
                    await self.stagehand.page.screenshot(
                        path=file_path,
                        timeout=10000  # Even shorter timeout for fallback
                    )
                    logger.info("Fallback screenshot (viewport only) succeeded")
                except Exception as fallback_error:
                    logger.warning(f"Fallback screenshot failed: {fallback_error}")
                    
                    # Final fallback: Try with minimal options
                    await self.stagehand.page.screenshot(
                        path=file_path,
                        timeout=5000,
                        clip={"x": 0, "y": 0, "width": 1280, "height": 720}  # Fixed viewport clip
                    )
                    logger.info("Minimal screenshot succeeded")
            
            self.screenshot_counter += 1
            logger.info(f"Screenshot {self.screenshot_counter} saved to: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"All screenshot attempts failed: {e}")
            raise
            
    async def take_timestamped_screenshot(self, directory: str, prefix: str = "screenshot") -> str:
        """Take a screenshot with timestamp in filename"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # milliseconds
        filename = f"{prefix}_{timestamp}_{self.screenshot_counter:03d}.png"
        file_path = os.path.join(directory, filename)
        return await self.take_screenshot(file_path)
        
    async def wait_and_screenshot(self, directory: str, wait_time: float = 1.0, prefix: str = "step") -> str:
        """Wait for page to settle and take screenshot with security measures"""
        # Use smart delay instead of fixed sleep
        await smart_delay(wait_time, wait_time + 1.0)
        
        try:
            await self.stagehand.page.wait_for_load_state("networkidle", timeout=5000)  # Reduced timeout
        except Exception as e:
            logger.warning(f"NetworkIdle timeout, proceeding anyway: {e}")
            
        return await self.take_timestamped_screenshot(directory, prefix)
    
    async def safe_screenshot(self, directory: str, wait_time: float = 1.0, prefix: str = "step") -> Optional[str]:
        """Safe screenshot that returns None on failure instead of raising exception"""
        try:
            return await self.wait_and_screenshot(directory, wait_time, prefix)
        except Exception as e:
            logger.warning(f"Safe screenshot failed for {prefix}: {e}")
            return None
            
    async def get_current_url(self) -> str:
        """Get current page URL"""
        if not self.stagehand:
            raise RuntimeError("Stagehand client not initialized")
            
        return self.stagehand.page.url
        
    async def wait_for_selector(self, selector: str, timeout: int = 10000) -> None:
        """Wait for a selector to appear on the page"""
        if not self.stagehand:
            raise RuntimeError("Stagehand client not initialized")
            
        try:
            await self.stagehand.page.wait_for_selector(selector, timeout=timeout)
            logger.info(f"Selector found: {selector}")
        except Exception as e:
            logger.error(f"Selector not found: {selector} - {e}")
            raise