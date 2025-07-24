import asyncio
import logging
import os
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
                
    async def navigate_to_url(self, url: str) -> None:
        """Navigate to a specific URL with security measures and retry logic"""
        if not self.stagehand:
            raise RuntimeError("Stagehand client not initialized")
        
        for attempt in range(settings.MAX_RETRIES):
            try:
                # Smart delay before navigation
                await smart_delay(1.0, 3.0)
                
                await self.stagehand.page.goto(url)
                await self.stagehand.page.wait_for_load_state("networkidle")
                
                # Check for blocking scenarios
                page_content = await self.stagehand.page.content()
                if await handle_blocking_scenario(page_content):
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
            result = await self.stagehand.act(instruction)
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
            if schema:
                result = await self.stagehand.extract(instruction, schema=schema)
            else:
                result = await self.stagehand.extract(instruction)
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
        """Take a screenshot of the current page"""
        if not self.stagehand:
            raise RuntimeError("Stagehand client not initialized")
            
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Take screenshot with consistent settings
            await self.stagehand.page.screenshot(
                path=file_path, 
                full_page=full_page,
                quality=95
            )
            
            self.screenshot_counter += 1
            logger.info(f"Screenshot {self.screenshot_counter} saved to: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
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
            await self.stagehand.page.wait_for_load_state("networkidle", timeout=10000)
        except Exception as e:
            logger.warning(f"NetworkIdle timeout, proceeding anyway: {e}")
            
        return await self.take_timestamped_screenshot(directory, prefix)
            
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