#!/usr/bin/env python3
"""
Zoopla Automation Main Script
Complete end-to-end Zoopla property search automation with video generation

Usage:
    python main.py <city_name>
    
Example:
    python main.py Manchester
    python main.py "Greater London"
    python main.py Birmingham
"""

import asyncio
import logging
import os
import sys
import json
from pathlib import Path
from automation.browserbase_client import BrowserbaseClient
from automation.screenshot_manager import ScreenshotManager
from utils.video_generator import VideoGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/main_automation.log')
    ]
)
logger = logging.getLogger(__name__)

async def run_zoopla_automation(city_name: str):
    """
    Run complete Zoopla automation workflow for the specified city
    
    Args:
        city_name (str): Name of the city to search for properties
        
    Returns:
        dict: Results including video path, screenshots, and property data
    """
    logger.info(f"=� Starting Zoopla automation for: {city_name}")
    
    results = {
        'city': city_name,
        'success': False,
        'screenshots': [],
        'video_path': None,
        'property_url': None,
        'session_directory': None,
        'steps_completed': [],
        'total_screenshots': 0
    }
    
    try:
        # Initialize components
        screenshot_manager = ScreenshotManager("zoopla_automation")
        session_dir = screenshot_manager.create_session_directory(city_name)
        video_generator = VideoGenerator("videos")
        
        # Ensure logs directory exists
        os.makedirs("logs", exist_ok=True)
        
        logger.info(f"=� Session directory: {session_dir}")
        
        async with BrowserbaseClient() as client:
            
            # Step 1: Navigate to Zoopla homepage
            logger.info("=� Step 1: Navigating to Zoopla homepage...")
            
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
            
            logger.info(" Step 1 completed - Successfully reached Zoopla")
            
            # Step 2: Search for city
            logger.info(f"=
 Step 2: Searching for '{city_name}'...")
            
            # Step 2a: Type in search box
            type_instruction = f"Type '{city_name}' in the location search box"
            await client.act(type_instruction)
            await asyncio.sleep(1)  # Brief pause
            
            # Screenshot after typing (shows city typed in search box)
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
            
            logger.info(f" Step 2 completed - Search for '{city_name}' executed")
            
            # Step 3: Navigate to property listings
            logger.info("<� Step 3: Accessing property listings...")
            
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
            
            logger.info(" Step 3 completed - Property listings accessed")
            
            # Step 4: Scroll through properties
            logger.info("=� Step 4: Scrolling through properties...")
            
            for i in range(1):
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
            logger.info(" Step 4 completed - Property scrolling done")
            
            # Step 5: Select a property
            logger.info("<� Step 5: Selecting a property...")
            
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
                
                logger.info(f" Step 5 completed - Property selected: {property_url}")
                
            except Exception as e:
                logger.warning(f"Property selection failed: {e}")
                # Continue with what we have
            
            # Get session metadata before generating video
            session_metadata = screenshot_manager.get_screenshot_metadata()
            results['session_directory'] = session_dir
            results['total_screenshots'] = len(results['screenshots'])
        
        # Step 6: Generate video from screenshots
        logger.info("<� Step 6: Generating video from screenshots...")
        
        try:
            video_path = video_generator.generate_video_from_session(session_metadata)
            
            if video_path:
                results['video_path'] = video_path
                video_info = video_generator.get_video_info(video_path)
                if video_info:
                    logger.info(f" Video generated: {video_info['filename']}")
                    logger.info(f"   - Size: {video_info['size_mb']} MB")
                    logger.info(f"   - Duration: {video_info.get('duration_seconds', 'unknown')} seconds")
                    results['video_info'] = video_info
                results['steps_completed'].append("Generate video")
            else:
                logger.warning("L Video generation failed")
                
        except Exception as e:
            logger.error(f"Video generation error: {e}")
        
        # Mark as successful
        results['success'] = True
        
        # Save results to JSON file
        results_file = f"automation_results_{city_name.lower().replace(' ', '_')}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"=� Results saved to: {results_file}")
        
        return results
        
    except Exception as e:
        logger.error(f"L Automation failed for {city_name}: {e}")
        results['error'] = str(e)
        return results

def print_results_summary(results: dict):
    """Print a comprehensive summary of the automation results"""
    
    print("\n" + "="*70)
    print("<� ZOOPLA AUTOMATION COMPLETED!")
    print("="*70)
    
    print(f"=� City Searched: {results['city']}")
    print(f" Success: {'Yes' if results['success'] else 'No'}")
    print(f"=� Screenshots Captured: {results['total_screenshots']}")
    print(f"=� Session Directory: {results['session_directory']}")
    
    if results.get('video_path'):
        print(f"<� Generated Video: {results['video_path']}")
        if results.get('video_info'):
            print(f"   =� Video Size: {results['video_info']['size_mb']} MB")
            print(f"   �  Duration: {results['video_info'].get('duration_seconds', 'unknown')} seconds")
    else:
        print("<� Generated Video: L Failed to generate")
    
    if results.get('property_url'):
        print(f"<� Property Selected: {results['property_url']}")
    else:
        print("<� Property Selected: L No property selected")
    
    print(f"\n=� Steps Completed ({len(results['steps_completed'])}/6):")
    for i, step in enumerate(results['steps_completed'], 1):
        print(f"   {i}.  {step}")
    
    # Show remaining steps if any failed
    all_steps = [
        "Navigate to Zoopla", "Search for city", "Access property listings",
        "Scroll through properties", "Select property", "Generate video"
    ]
    remaining_steps = [step for step in all_steps if step not in results['steps_completed']]
    if remaining_steps:
        print(f"\n�  Incomplete Steps:")
        for step in remaining_steps:
            print(f"   " {step}")
    
    if results.get('error'):
        print(f"\nL Error: {results['error']}")
    
    print("\n" + "="*70)
    
    # Print the video path prominently at the end
    if results.get('video_path'):
        print(f"\n<� GENERATED VIDEO FILE:")
        print(f"   {os.path.abspath(results['video_path'])}")
        print("="*70)

def main():
    """Main function - entry point for the automation"""
    
    # Check for city name argument
    if len(sys.argv) < 2:
        print("L Error: City name is required!")
        print("\nUsage:")
        print("   python main.py <city_name>")
        print("\nExamples:")
        print("   python main.py Manchester")
        print("   python main.py \"Greater London\"")
        print("   python main.py Birmingham")
        print("   python main.py Leeds")
        sys.exit(1)
    
    # Get city name from command line arguments
    city_name = " ".join(sys.argv[1:])  # Join all arguments in case city has spaces
    
    # Validate city name
    if not city_name.strip():
        print("L Error: City name cannot be empty!")
        sys.exit(1)
    
    print(f"<�  Starting Zoopla automation for: {city_name}")
    
    # Ensure required directories exist
    os.makedirs("videos", exist_ok=True)
    os.makedirs("zoopla_automation", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    try:
        # Run the automation
        results = asyncio.run(run_zoopla_automation(city_name))
        
        # Print comprehensive results
        print_results_summary(results)
        
        # Exit with appropriate code
        sys.exit(0 if results['success'] else 1)
        
    except KeyboardInterrupt:
        print("\n�  Automation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nL Automation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()