#!/usr/bin/env python3
"""
Quick test script for recipe websites.
Usage: python quick_test.py <recipe_url>
"""

import sys
import time
from scrape import scrape_recipe_page
from enhanced_scraping import scrape_recipe_page_enhanced

def quick_test(url):
    """Quick test of both scrapers on a single URL."""
    print(f"🧪 Quick Testing: {url}")
    print("=" * 50)
    
    # Test original scraper
    print("1. Testing original scraper...")
    start_time = time.time()
    result1 = scrape_recipe_page(url)
    time1 = time.time() - start_time
    
    if result1.startswith('Error scraping recipe:') or result1 == "No recipe content found":
        print(f"❌ Original scraper failed: {result1[:100]}...")
        success1 = False
    else:
        print(f"✅ Original scraper succeeded ({time1:.1f}s)")
        print(f"   Content length: {len(result1)} characters")
        success1 = True
    
    print()
    
    # Test enhanced scraper
    print("2. Testing enhanced scraper...")
    start_time = time.time()
    result2 = scrape_recipe_page_enhanced(url)
    time2 = time.time() - start_time
    
    if result2.startswith('Error scraping recipe:') or result2 == "No recipe content found":
        print(f"❌ Enhanced scraper failed: {result2[:100]}...")
        success2 = False
    else:
        print(f"✅ Enhanced scraper succeeded ({time2:.1f}s)")
        print(f"   Content length: {len(result2)} characters")
        success2 = True
    
    print()
    print("=" * 50)
    print("SUMMARY:")
    
    if success1 and success2:
        print("✅ Both scrapers work!")
        if len(result1) > len(result2):
            print("   Original scraper got more content")
        elif len(result2) > len(result1):
            print("   Enhanced scraper got more content")
        else:
            print("   Both scrapers got similar content")
    elif success1:
        print("✅ Only original scraper works")
    elif success2:
        print("✅ Only enhanced scraper works")
    else:
        print("❌ Both scrapers failed")
        print("   This site may have strong anti-bot protection")
    
    return success1 or success2

def main():
    if len(sys.argv) < 2:
        print("Usage: python quick_test.py <recipe_url>")
        print("Example: python quick_test.py https://www.allrecipes.com/recipe/12345")
        sys.exit(1)
    
    url = sys.argv[1]
    success = quick_test(url)
    
    if not success:
        print("\n💡 Suggestions:")
        print("   - Try a different recipe URL")
        print("   - Check if the site is accessible in a browser")
        print("   - Run 'python test_scraping.py <url>' for detailed analysis")
        sys.exit(1)

if __name__ == "__main__":
    main()
