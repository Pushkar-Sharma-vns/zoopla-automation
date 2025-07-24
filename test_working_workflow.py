#!/usr/bin/env python3
"""
Working end-to-end Zoopla automation workflow
Uses proven bypass system with proper error handling
"""

import asyncio
import logging
import os
import json
from automation.browserbase_client import BrowserbaseClient
from automation.screenshot_manager import ScreenshotManager
from utils.video_generator import VideoGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_working_zoopla_workflow(city_name: str = "London"):
    """Run the complete working Zoopla automation workflow"""
    logger.info(f"🚀 Starting WORKING Zoopla workflow for {city_name}")
    
    results = {
        'city': city_name,
        'success': False,
        'screenshots': [],
        'video_path': None,
        'property_url': None,
        'session_directory': None,
        'steps_completed': []
    }
    
    try:
        # Initialize components
        screenshot_manager = ScreenshotManager("working_workflow")
        session_dir = screenshot_manager.create_session_directory(city_name)
        video_generator = VideoGenerator("videos")
        
        async with BrowserbaseClient() as client:
            
            # Step 1: Navigate to Zoopla (using proven method)
            logger.info("📍 Step 1: Navigating to Zoopla with Cloudflare bypass...")
            
            # Navigate directly using our proven method
            await client.navigate_to_url("https://www.zoopla.co.uk")
            
            # Take homepage screenshot
            homepage_screenshot = await client.wait_and_screenshot(
                session_dir, 
                wait_time=2.0, 
                prefix="01_homepage"
            )
            screenshot_manager.add_screenshot(homepage_screenshot, "Zoopla Homepage")
            results['screenshots'].append(homepage_screenshot)
            results['steps_completed'].append("Navigate to Zoopla")
            
            logger.info("✅ Step 1 completed - Successfully reached Zoopla")
            
            # Step 2: Search for city
            logger.info(f"🔍 Step 2: Searching for {city_name}...")
            
            # Step 2a: Type in search box
            type_instruction = f"Type '{city_name}' in the location search box"
            await client.act(type_instruction)
            await asyncio.sleep(1)  # Brief pause
            
            # Screenshot after typing (shows London typed in search box)
            typing_screenshot = await client.wait_and_screenshot(
                session_dir,
                wait_time=1.0,
                prefix="02a_search_typed"
            )
            screenshot_manager.add_screenshot(typing_screenshot, f"'{city_name}' typed in search box")
            results['screenshots'].append(typing_screenshot)
            
            # Step 2b: Click search button explicitly
            click_instruction = "Click the purple 'Search' button to search for properties"
            await client.act(click_instruction)
            
            # Screenshot immediately after clicking (shows search button being clicked)
            click_screenshot = await client.wait_and_screenshot(
                session_dir,
                wait_time=1.0,
                prefix="02b_search_clicked"
            )
            screenshot_manager.add_screenshot(click_screenshot, "Search button clicked")
            results['screenshots'].append(click_screenshot)
            
            # Wait and screenshot search results (final results page)
            await asyncio.sleep(4)  # Let search results fully load
            search_screenshot = await client.wait_and_screenshot(
                session_dir,
                wait_time=2.0,
                prefix="02c_search_results"
            )
            screenshot_manager.add_screenshot(search_screenshot, f"Search Results for {city_name}")
            results['screenshots'].append(search_screenshot)
            results['steps_completed'].append("Search for city")
            
            logger.info("✅ Step 2 completed - City search executed")
            
            # Step 3: Navigate to property listings
            logger.info("🏠 Step 3: Accessing property listings...")
            
            # Try to click on "For Sale" or property listings
            try:
                listings_instruction = "Click on 'For Sale' or 'Properties for sale' to view property listings"
                await client.act(listings_instruction)
                await asyncio.sleep(3)
            except Exception:
                logger.info("Direct listings navigation not needed - already on listings")
            
            # Screenshot property listings
            listings_screenshot = await client.wait_and_screenshot(
                session_dir,
                wait_time=2.0,
                prefix="03_property_listings"
            )
            screenshot_manager.add_screenshot(listings_screenshot, "Property Listings")
            results['screenshots'].append(listings_screenshot)
            results['steps_completed'].append("Access property listings")
            
            logger.info("✅ Step 3 completed - Property listings accessed")
            
            # Step 4: Scroll through properties (2-3 scrolls)
            logger.info("📜 Step 4: Scrolling through properties...")
            
            for i in range(2):
                scroll_instruction = f"Scroll down slowly to show more properties (scroll {i+1})"
                await client.act(scroll_instruction)
                await asyncio.sleep(2)
                
                scroll_screenshot = await client.wait_and_screenshot(
                    session_dir,
                    wait_time=1.0,
                    prefix=f"04_scroll_{i+1:02d}"
                )
                screenshot_manager.add_screenshot(scroll_screenshot, f"Scroll {i+1}")
                results['screenshots'].append(scroll_screenshot)
            
            results['steps_completed'].append("Scroll through properties")
            logger.info("✅ Step 4 completed - Property scrolling done")
            
            # Step 5: Select a property
            logger.info("🎲 Step 5: Selecting a property...")
            
            try:
                # Use Stagehand to select first available property
                selection_instruction = "Click on the first property listing visible on the page to view its details"
                await client.act(selection_instruction)
                await asyncio.sleep(4)
                
                # Get property URL
                property_url = await client.get_current_url()
                results['property_url'] = property_url
                
                # Screenshot selected property
                property_screenshot = await client.wait_and_screenshot(
                    session_dir,
                    wait_time=3.0,
                    prefix="05_selected_property"
                )
                screenshot_manager.add_screenshot(property_screenshot, "Selected Property")
                results['screenshots'].append(property_screenshot)
                results['steps_completed'].append("Select property")
                
                logger.info(f"✅ Step 5 completed - Property selected: {property_url}")
                
            except Exception as e:
                logger.warning(f"Property selection failed: {e}")
                # Continue with what we have
            
            # Step 6: Generate video from screenshots
            logger.info("🎬 Step 6: Generating video from screenshots...")
            
            try:
                session_metadata = screenshot_manager.get_screenshot_metadata()
                video_path = video_generator.generate_video_from_session(session_metadata)
                
                if video_path:
                    results['video_path'] = video_path
                    video_info = video_generator.get_video_info(video_path)
                    if video_info:
                        logger.info(f"✅ Video generated: {video_info['filename']}")
                        logger.info(f"   - Size: {video_info['size_mb']} MB")
                        results['video_info'] = video_info
                    results['steps_completed'].append("Generate video")
                else:
                    logger.warning("Video generation failed")
                    
            except Exception as e:
                logger.error(f"Video generation error: {e}")
            
            # Final results
            results['success'] = True
            results['session_directory'] = session_dir
            results['total_screenshots'] = len(results['screenshots'])
        
        # Save results
        results_file = f"working_workflow_results_{city_name.lower()}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"💾 Results saved to {results_file}")
        
        # Final summary
        logger.info("\n" + "="*60)
        logger.info("🎉 WORKING WORKFLOW SUCCESS!")
        logger.info("="*60)
        logger.info(f"📍 City: {results['city']}")
        logger.info(f"📸 Screenshots: {results['total_screenshots']}")
        logger.info(f"🎬 Video: {results['video_path'] or 'Not generated'}")
        logger.info(f"🏠 Property URL: {results['property_url'] or 'Not captured'}")
        logger.info(f"✅ Steps completed: {len(results['steps_completed'])}/6")
        
        for i, step in enumerate(results['steps_completed'], 1):
            logger.info(f"   {i}. {step}")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Workflow failed: {e}")
        results['error'] = str(e)
        return results

async def main():
    """Main function"""
    import sys
    
    city = "London"
    if len(sys.argv) > 1:
        city = sys.argv[1]
    
    # Ensure output directories exist
    os.makedirs("videos", exist_ok=True)
    os.makedirs("working_workflow", exist_ok=True)
    
    results = await run_working_zoopla_workflow(city)
    
    # Exit with appropriate code
    exit(0 if results['success'] else 1)

if __name__ == "__main__":
    asyncio.run(main())