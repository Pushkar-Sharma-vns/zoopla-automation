#!/usr/bin/env python3
"""
Test script for Zoopla automation flow
Tests the complete system from Browserbase connection to Zoopla navigation
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from automation.browserbase_client import BrowserbaseClient
from automation.screenshot_manager import ScreenshotManager
from automation.zoopla_navigator import ZooplaNavigator
from config.settings import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/test_flow.log')
    ]
)
logger = logging.getLogger(__name__)

class ZooplaFlowTester:
    def __init__(self):
        self.test_city = "London"  # Test with London as it's most likely to have results
        self.results = {}
        
    async def test_environment_setup(self) -> bool:
        """Test that environment variables are properly configured"""
        logger.info("🔧 Testing environment setup...")
        
        try:
            settings.validate()
            logger.info("✅ Environment variables validated successfully")
            logger.info(f"   - Browserbase API Key: {'*' * 20}{settings.BROWSERBASE_API_KEY[-8:]}")
            logger.info(f"   - Project ID: {settings.BROWSERBASE_PROJECT_ID}")
            logger.info(f"   - Model: {settings.MODEL_NAME}")
            return True
        except Exception as e:
            logger.error(f"❌ Environment validation failed: {e}")
            return False
            
    async def test_browserbase_connection(self) -> bool:
        """Test Browserbase client initialization and connection"""
        logger.info("🌐 Testing Browserbase connection...")
        
        try:
            async with BrowserbaseClient() as client:
                await client.navigate_to_url("https://www.google.com")
                current_url = await client.get_current_url()
                
                if "google.com" in current_url:
                    logger.info("✅ Browserbase connection successful")
                    logger.info(f"   - Session ID: {client.session_id}")
                    logger.info(f"   - Current URL: {current_url}")
                    return True
                else:
                    logger.error(f"❌ Unexpected URL: {current_url}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Browserbase connection failed: {e}")
            return False
            
    async def test_screenshot_functionality(self) -> bool:
        """Test screenshot capture and management"""
        logger.info("📸 Testing screenshot functionality...")
        
        try:
            # Create screenshot manager
            screenshot_manager = ScreenshotManager("test_screenshots")
            session_dir = screenshot_manager.create_session_directory("test")
            
            async with BrowserbaseClient() as client:
                # Navigate to a simple page
                await client.navigate_to_url("https://example.com")
                
                # Test screenshot capture
                screenshot_path = await client.wait_and_screenshot(
                    session_dir, 
                    wait_time=1.0, 
                    prefix="test"
                )
                
                # Verify screenshot exists
                if os.path.exists(screenshot_path):
                    logger.info("✅ Screenshot functionality working")
                    logger.info(f"   - Screenshot saved: {screenshot_path}")
                    logger.info(f"   - File size: {os.path.getsize(screenshot_path)} bytes")
                    
                    # Add to manager and validate
                    screenshot_manager.add_screenshot(screenshot_path, "Test screenshot")
                    validation = screenshot_manager.validate_screenshots()
                    
                    if validation["valid_count"] > 0:
                        logger.info(f"   - Screenshot validation: {validation['valid_count']} valid")
                        return True
                    else:
                        logger.error("❌ Screenshot validation failed")
                        return False
                else:
                    logger.error(f"❌ Screenshot file not created: {screenshot_path}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Screenshot functionality failed: {e}")
            return False
            
    async def test_zoopla_navigation(self) -> bool:
        """Test complete Zoopla navigation flow"""
        logger.info(f"🏠 Testing Zoopla navigation with city: {self.test_city}")
        
        try:
            screenshot_manager = ScreenshotManager("test_zoopla")
            
            async with BrowserbaseClient() as client:
                navigator = ZooplaNavigator(client, screenshot_manager)
                
                # Test step by step
                logger.info("   - Step 1: Navigate to Zoopla homepage")
                await navigator.navigate_to_zoopla()
                
                logger.info(f"   - Step 2: Search for city '{self.test_city}'")
                await navigator.search_city(self.test_city)
                
                logger.info("   - Step 3: Handle property listings")
                await navigator.handle_property_listings()
                
                logger.info("   - Step 4: Scroll and capture screenshots")
                scroll_screenshots = await navigator.scroll_and_capture(scroll_count=2)
                
                logger.info("   - Step 5: Select random property")
                property_info = await navigator.select_random_property()
                
                logger.info("   - Step 6: Capture property details")
                await navigator.capture_property_details()
                
                # Get final results
                metadata = screenshot_manager.get_screenshot_metadata()
                
                logger.info("✅ Zoopla navigation completed successfully")
                logger.info(f"   - Total screenshots: {metadata['screenshot_count']}")
                logger.info(f"   - Property URL: {property_info.get('property_url', 'N/A')}")
                logger.info(f"   - Session directory: {metadata['session_directory']}")
                
                self.results['navigation'] = {
                    'success': True,
                    'screenshots': metadata['screenshot_count'],
                    'property_url': property_info.get('property_url'),
                    'session_dir': metadata['session_directory']
                }
                
                return True
                
        except Exception as e:
            logger.error(f"❌ Zoopla navigation failed: {e}")
            self.results['navigation'] = {'success': False, 'error': str(e)}
            return False
            
    async def test_complete_flow(self) -> bool:
        """Test the complete automation flow"""
        logger.info(f"🚀 Testing complete Zoopla automation flow for {self.test_city}")
        
        try:
            screenshot_manager = ScreenshotManager("complete_test")
            
            async with BrowserbaseClient() as client:
                navigator = ZooplaNavigator(client, screenshot_manager)
                
                # Run complete flow
                result = await navigator.complete_navigation_flow(self.test_city)
                
                logger.info("✅ Complete flow executed successfully")
                logger.info(f"   - City: {result['city']}")
                logger.info(f"   - Total screenshots: {result['total_screenshots']}")
                logger.info(f"   - Property URL: {result['property_info']['property_url']}")
                logger.info(f"   - Session directory: {result['screenshot_session']}")
                
                self.results['complete_flow'] = result
                return True
                
        except Exception as e:
            logger.error(f"❌ Complete flow failed: {e}")
            self.results['complete_flow'] = {'success': False, 'error': str(e)}
            return False
            
    async def run_all_tests(self) -> dict:
        """Run all tests and return results"""
        logger.info("🧪 Starting Zoopla Automation Flow Tests")
        logger.info("=" * 60)
        
        # Ensure directories exist
        os.makedirs("logs", exist_ok=True)
        os.makedirs("test_screenshots", exist_ok=True)
        os.makedirs("test_zoopla", exist_ok=True)
        
        test_results = {}

        # Run tests in sequence
        tests = [
            # ("Environment Setup", self.test_environment_setup),
            # ("Browserbase Connection", self.test_browserbase_connection),
            # ("Screenshot Functionality", self.test_screenshot_functionality),
            ("Zoopla Navigation", self.test_zoopla_navigation),
            # ("Complete Flow", self.test_complete_flow)
        ]
        
        for test_name, test_func in tests:
            logger.info(f"\n{'=' * 20} {test_name} {'=' * 20}")
            try:
                success = await test_func()
                test_results[test_name] = {
                    'success': success,
                    'status': '✅ PASSED' if success else '❌ FAILED'
                }
            except Exception as e:
                logger.error(f"❌ Test '{test_name}' crashed: {e}")
                test_results[test_name] = {
                    'success': False,
                    'status': '💥 CRASHED',
                    'error': str(e)
                }
        
        # Print final summary
        logger.info("\n" + "=" * 60)
        logger.info("📊 TEST SUMMARY")
        logger.info("=" * 60)
        
        passed = sum(1 for result in test_results.values() if result['success'])
        total = len(test_results)
        
        for test_name, result in test_results.items():
            logger.info(f"{result['status']} {test_name}")
            if 'error' in result:
                logger.info(f"   Error: {result['error']}")
        
        logger.info(f"\nResults: {passed}/{total} tests passed")
        
        if passed == total:
            logger.info("🎉 All tests passed! The system is working correctly.")
        else:
            logger.error(f"❌ {total - passed} tests failed. Check logs for details.")
            
        return test_results

async def main():
    """Main test runner"""
    tester = ZooplaFlowTester()
    results = await tester.run_all_tests()
    
    # Exit with appropriate code
    all_passed = all(result['success'] for result in results.values())
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    asyncio.run(main())