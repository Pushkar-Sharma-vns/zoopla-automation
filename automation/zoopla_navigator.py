import asyncio
import logging
import random
from typing import Dict, Any, Optional, List
from automation.browserbase_client import BrowserbaseClient
from automation.screenshot_manager import ScreenshotManager
from config.settings import settings
from utils.security_utils import (
    smart_delay, scroll_delay, click_delay, page_load_wait, 
    city_search_throttle, handle_blocking_scenario
)

logger = logging.getLogger(__name__)

class ZooplaNavigator:
    def __init__(self, client: BrowserbaseClient, screenshot_manager: ScreenshotManager):
        self.client = client
        self.screenshot_manager = screenshot_manager
        self.base_url = settings.ZOOPLA_BASE_URL
        self.current_city: Optional[str] = None
        
    async def navigate_to_zoopla(self) -> str:
        """Navigate to Zoopla homepage with security measures"""
        try:
            logger.info("🏠 Navigating to Zoopla homepage...")
            await self.client.navigate_to_url(self.base_url)
            
            # Wait for page to fully load like a human would
            await page_load_wait()
            
            screenshot_path = await self.client.wait_and_screenshot(
                self.screenshot_manager.get_session_directory(), 
                wait_time=3.0, 
                prefix="01_homepage"
            )
            self.screenshot_manager.add_screenshot(screenshot_path, "Zoopla Homepage")
            
            logger.info(f"✅ Successfully navigated to Zoopla: {self.base_url}")
            return screenshot_path
            
        except Exception as e:
            logger.error(f"❌ Failed to navigate to Zoopla: {e}")
            raise
            
    async def search_city(self, city: str) -> str:
        """Search for a specific city with respectful rate limiting"""
        self.current_city = city
        
        try:
            # Apply city search throttling (max 1 per 10-15 seconds)
            await city_search_throttle()
            
            logger.info(f"🔍 Searching for city: {city}")
            
            # Human-like delay before interacting
            await click_delay()
            
            # Use Stagehand to search for the city
            search_instruction = f"Search for properties in {city} by finding the search box and entering '{city}', then click search or press enter"
            await self.client.act(search_instruction)
            
            # Wait for search results with human-like timing
            await page_load_wait()
            await self.client.stagehand.page.wait_for_load_state("networkidle", timeout=15000)
            
            # Check for blocking scenarios
            page_content = await self.client.stagehand.page.content()
            page_title = await self.client.stagehand.page.title()
            if await handle_blocking_scenario(page_content, page_title):
                logger.warning("🚨 Blocking detected during city search")
                raise Exception("Blocking scenario detected during search")
            
            # Take screenshot of search results
            screenshot_path = await self.client.wait_and_screenshot(
                self.screenshot_manager.get_session_directory(),
                wait_time=3.0,
                prefix="02_search_results"
            )
            self.screenshot_manager.add_screenshot(screenshot_path, f"Search Results for {city}")
            
            logger.info(f"✅ Successfully searched for city: {city}")
            return screenshot_path
            
        except Exception as e:
            logger.error(f"❌ Failed to search for city {city}: {e}")
            raise
            
    async def handle_property_listings(self) -> str:
        """Navigate to property listings page and take screenshot"""
        try:
            # Check if we're already on a listings page or need to navigate
            current_url = await self.client.get_current_url()
            
            if "property" not in current_url.lower() and "for-sale" not in current_url.lower():
                # Try to click on "For Sale" or similar property listings link
                listings_instruction = "Click on 'For Sale' or 'Properties for sale' to view property listings"
                await self.client.act(listings_instruction)
                await asyncio.sleep(2.0)
                
            # Wait for listings to load
            await self.client.stagehand.page.wait_for_load_state("networkidle", timeout=10000)
            
            # Take screenshot of property listings
            screenshot_path = await self.client.wait_and_screenshot(
                self.screenshot_manager.get_session_directory(),
                wait_time=2.0,
                prefix="03_property_listings"
            )
            self.screenshot_manager.add_screenshot(screenshot_path, "Property Listings Page")
            
            logger.info("Successfully navigated to property listings")
            return screenshot_path
            
        except Exception as e:
            logger.error(f"Failed to handle property listings: {e}")
            raise
            
    async def scroll_and_capture(self, scroll_count: int = 3) -> List[str]:
        """Scroll through the page with human-like behavior and capture screenshots"""
        screenshots = []
        
        try:
            logger.info(f"📜 Starting scroll and capture ({scroll_count} scrolls)")
            
            for i in range(scroll_count):
                # Human-like scroll delay
                await scroll_delay()
                
                # Scroll down with variation
                scroll_instruction = f"Scroll down slowly to show more properties (scroll {i+1})"
                await self.client.act(scroll_instruction)
                
                # Wait for content to load and settle
                await smart_delay(2.0, 4.0)
                
                screenshot_path = await self.client.wait_and_screenshot(
                    self.screenshot_manager.get_session_directory(),
                    wait_time=2.0,
                    prefix=f"04_scroll_{i+1:02d}"
                )
                self.screenshot_manager.add_screenshot(screenshot_path, f"Scroll {i+1}")
                screenshots.append(screenshot_path)
                
                logger.info(f"📸 Captured scroll screenshot {i+1}/{scroll_count}")
                
            logger.info(f"✅ Completed {scroll_count} scroll captures")
            return screenshots
            
        except Exception as e:
            logger.error(f"❌ Failed during scroll and capture: {e}")
            raise
            
    async def select_random_property(self) -> Dict[str, Any]:
        """Select a random property with human-like behavior"""
        try:
            logger.info("🏡 Selecting random property...")
            
            # Human-like delay before observing
            await smart_delay(2.0, 4.0)
            
            # First, observe the page to understand the property listings
            observation = await self.client.observe(
                "Describe the property listings visible on this page, including how many properties are shown"
            )
            logger.info(f"Page observation: {observation}")
            
            # Get a random property (1-6 range for safety)
            random_selection = random.randint(1, 6)
            
            # Human-like delay before clicking
            await click_delay()
            
            # Select a property using natural language
            selection_instruction = f"Click on the {self._get_ordinal(random_selection)} property listing visible on the page to view its details"
            
            logger.info(f"🎲 Attempting to select {self._get_ordinal(random_selection)} property")
            await self.client.act(selection_instruction)
            
            # Wait for property page to load with human-like timing
            await page_load_wait()
            await self.client.stagehand.page.wait_for_load_state("networkidle", timeout=15000)
            
            # Check for blocking scenarios
            page_content = await self.client.stagehand.page.content()
            page_title = await self.client.stagehand.page.title()
            if await handle_blocking_scenario(page_content, page_title):
                logger.warning("🚨 Blocking detected during property selection")
                raise Exception("Blocking scenario detected during property selection")
            
            # Take screenshot of selected property
            screenshot_path = await self.client.wait_and_screenshot(
                self.screenshot_manager.get_session_directory(),
                wait_time=3.0,
                prefix="05_selected_property"
            )
            self.screenshot_manager.add_screenshot(screenshot_path, "Selected Property Details")
            
            # Get property URL for reference
            property_url = await self.client.get_current_url()
            
            logger.info(f"✅ Successfully selected random property: {property_url}")
            
            return {
                "property_url": property_url,
                "screenshot_path": screenshot_path,
                "selection_number": random_selection
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to select random property: {e}")
            raise
            
    async def capture_property_details(self) -> str:
        """Scroll through property page and capture additional screenshots"""
        try:
            screenshots = []
            
            # Capture property images/gallery
            gallery_instruction = "Scroll through or view property images if there are any galleries or image carousels"
            try:
                await self.client.act(gallery_instruction)
                await asyncio.sleep(2.0)
                screenshot_path = await self.client.wait_and_screenshot(
                    self.screenshot_manager.get_session_directory(),
                    wait_time=1.0,
                    prefix="06_property_gallery"
                )
                self.screenshot_manager.add_screenshot(screenshot_path, "Property Gallery")
                screenshots.append(screenshot_path)
            except Exception as e:
                logger.warning(f"Could not capture property gallery: {e}")
                
            # Scroll down to see more details
            for i in range(2):
                scroll_instruction = "Scroll down to see more property details, description, and features"
                await self.client.act(scroll_instruction)
                await asyncio.sleep(1.5)
                
                screenshot_path = await self.client.wait_and_screenshot(
                    self.screenshot_manager.get_session_directory(),
                    wait_time=1.0,
                    prefix=f"07_property_details_{i+1:02d}"
                )
                self.screenshot_manager.add_screenshot(screenshot_path, f"Property Details {i+1}")
                screenshots.append(screenshot_path)
                
            logger.info(f"Captured {len(screenshots)} additional property screenshots")
            return screenshots[-1] if screenshots else ""
            
        except Exception as e:
            logger.error(f"Failed to capture property details: {e}")
            raise
            
    def _get_ordinal(self, number: int) -> str:
        """Convert number to ordinal (1st, 2nd, 3rd, etc.)"""
        if 10 <= number % 100 <= 20:
            suffix = 'th'
        else:
            suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(number % 10, 'th')
        return f"{number}{suffix}"
        
    async def complete_navigation_flow(self, city: str) -> Dict[str, Any]:
        """Complete the full navigation flow for a city"""
        try:
            # Create session directory
            session_dir = self.screenshot_manager.create_session_directory(city)
            
            # Step 1: Navigate to Zoopla
            await self.navigate_to_zoopla()
            
            # Step 2: Search for city
            await self.search_city(city)
            
            # Step 3: Handle property listings
            await self.handle_property_listings()
            
            # Step 4: Scroll and capture for video
            await self.scroll_and_capture(scroll_count=3)
            
            # Step 5: Select random property
            property_info = await self.select_random_property()
            
            # Step 6: Capture property details
            await self.capture_property_details()
            
            # Get final screenshot metadata
            screenshot_metadata = self.screenshot_manager.get_screenshot_metadata()
            
            return {
                "city": city,
                "property_info": property_info,
                "screenshot_session": session_dir,
                "screenshot_metadata": screenshot_metadata,
                "total_screenshots": len(screenshot_metadata["screenshots"])
            }
            
        except Exception as e:
            logger.error(f"Failed to complete navigation flow for {city}: {e}")
            raise