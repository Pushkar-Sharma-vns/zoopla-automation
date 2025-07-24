#!/usr/bin/env python3
"""
Natural Cloudflare bypass - let the challenge complete naturally, then extract cookies
"""

import asyncio
import logging
import json
from automation.browserbase_client import BrowserbaseClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_natural_cloudflare_bypass():
    """Complete Cloudflare challenge naturally and extract working cookies"""
    logger.info("🌟 Testing natural Cloudflare bypass - allowing challenge to complete...")
    
    try:
        async with BrowserbaseClient() as client:
            page = client.stagehand.page
            context = page.context
            
            # Navigate to Zoopla and let Cloudflare run its course
            logger.info("🚀 Navigating to Zoopla and waiting for natural challenge completion...")
            
            await page.goto("https://www.zoopla.co.uk", 
                           wait_until="domcontentloaded", 
                           timeout=60000)
            
            # Monitor the page until Cloudflare completes
            challenge_completed = False
            max_attempts = 24  # 2 minutes total (24 * 5 seconds)
            
            for attempt in range(max_attempts):
                await asyncio.sleep(5)
                
                title = await page.title()
                current_url = page.url
                
                logger.info(f"Attempt {attempt + 1}/{max_attempts}: Title='{title}'")
                
                # Check if Cloudflare challenge is done
                if "just a moment" not in title.lower() and "cloudflare" not in title.lower():
                    if "zoopla" in title.lower() or "property" in title.lower() or len(title) > 10:
                        logger.info("🎉 Cloudflare challenge appears to be completed!")
                        challenge_completed = True
                        break
                
                # Simulate human-like behavior during wait
                if attempt % 4 == 0:  # Every 4th attempt (20 seconds)
                    try:
                        # Small random mouse movement
                        viewport = await page.evaluate("() => ({ width: window.innerWidth, height: window.innerHeight })")
                        await page.mouse.move(
                            viewport["width"] // 2 + (attempt % 100) - 50,
                            viewport["height"] // 2 + (attempt % 80) - 40
                        )
                        logger.info("🖱️ Simulated human mouse movement")
                    except:
                        pass
            
            if not challenge_completed:
                logger.warning("⚠️ Cloudflare challenge did not complete in time")
                
            # Extract current cookies regardless of completion status
            cookies = await context.cookies()
            
            logger.info(f"📋 Extracted {len(cookies)} cookies from session:")
            
            cloudflare_cookies = []
            zoopla_cookies = []
            
            for cookie in cookies:
                cookie_info = f"  {cookie['name']}: {cookie['value'][:30]}..."
                
                if any(cf_name in cookie['name'].lower() for cf_name in ['cf_', '_cf', 'cloudflare']):
                    cloudflare_cookies.append(cookie)
                    logger.info(f"🔥 CF Cookie: {cookie_info}")
                elif 'zoopla' in cookie['name'].lower() or 'zpg' in cookie['name'].lower():
                    zoopla_cookies.append(cookie)
                    logger.info(f"🏠 Zoopla Cookie: {cookie_info}")
                else:
                    logger.info(f"📋 Other Cookie: {cookie_info}")
            
            # Save cookies to file for future use
            all_cookies = {
                'cloudflare_cookies': cloudflare_cookies,
                'zoopla_cookies': zoopla_cookies,
                'all_cookies': cookies,
                'session_info': {
                    'title': await page.title(),
                    'url': page.url,
                    'challenge_completed': challenge_completed
                }
            }
            
            with open('extracted_cookies.json', 'w') as f:
                json.dump(all_cookies, f, indent=2)
            logger.info("💾 Saved cookies to extracted_cookies.json")
            
            # Test current page state
            search_elements = await page.query_selector_all('[placeholder*="search" i], [name*="search" i], .search-box, input[type="search"]')
            property_elements = await page.query_selector_all('[href*="property" i], .property, [class*="listing" i]')
            
            logger.info(f"🔍 Found {len(search_elements)} search elements")
            logger.info(f"🏠 Found {len(property_elements)} property elements")
            
            # Take screenshot
            screenshot_path = "natural_bypass_result.png"
            await page.screenshot(path=screenshot_path, full_page=True)
            logger.info(f"📸 Screenshot saved: {screenshot_path}")
            
            # Evaluate success
            current_title = await page.title()
            success_indicators = [
                challenge_completed,
                len(cloudflare_cookies) > 0,
                len(search_elements) > 0 or len(property_elements) > 0,
                "just a moment" not in current_title.lower(),
                len(current_title) > 10
            ]
            
            success_count = sum(success_indicators)
            logger.info(f"✅ Success indicators: {success_count}/5")
            
            # Even partial success gives us valuable cookie data
            if success_count >= 2:
                logger.info("🎉 SUCCESS: Obtained valuable cookie data!")
                
                # Display key cookies for manual analysis
                logger.info("\n🔑 KEY COOKIES FOR MANUAL REVIEW:")
                for cf_cookie in cloudflare_cookies[:3]:  # Show first 3 CF cookies
                    logger.info(f"  {cf_cookie['name']}: {cf_cookie['value']}")
                
                return True
            else:
                logger.warning("⚠️ Limited success - review cookies for potential use")
                return False
                
    except Exception as e:
        logger.error(f"💥 Test crashed: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_natural_cloudflare_bypass())
    exit(0 if result else 1)