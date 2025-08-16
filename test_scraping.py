#!/usr/bin/env python3
"""
Test script for debugging recipe website scraping issues.
This script helps you test different websites locally and identify blocking issues.
"""

import sys
import os
import time
import json
from urllib.parse import urlparse
from scrape import scrape_recipe_page, scrape_with_selenium
import requests
from fake_useragent import UserAgent
import cloudscraper

def test_basic_request(url: str) -> dict:
    """Test basic HTTP request to see if the site is accessible."""
    print(f"\n🔍 Testing basic HTTP request to: {url}")
    
    try:
        # Test with regular requests
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        print(f"✅ Regular requests: Status {response.status_code}")
        print(f"   Content length: {len(response.content)} bytes")
        print(f"   Content type: {response.headers.get('content-type', 'unknown')}")
        
        return {
            'status': 'success',
            'status_code': response.status_code,
            'content_length': len(response.content),
            'content_type': response.headers.get('content-type'),
            'headers': dict(response.headers)
        }
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Regular requests failed: {str(e)}")
        return {
            'status': 'failed',
            'error': str(e)
        }

def test_cloudscraper(url: str) -> dict:
    """Test cloudscraper to bypass potential blocking."""
    print(f"\n🌐 Testing cloudscraper for: {url}")
    
    try:
        scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False
            },
            delay=10
        )
        
        response = scraper.get(url, timeout=30)
        print(f"✅ Cloudscraper: Status {response.status_code}")
        print(f"   Content length: {len(response.content)} bytes")
        print(f"   Content type: {response.headers.get('content-type', 'unknown')}")
        
        return {
            'status': 'success',
            'status_code': response.status_code,
            'content_length': len(response.content),
            'content_type': response.headers.get('content-type')
        }
        
    except Exception as e:
        print(f"❌ Cloudscraper failed: {str(e)}")
        return {
            'status': 'failed',
            'error': str(e)
        }

def test_selenium(url: str) -> dict:
    """Test Selenium scraping (if available)."""
    print(f"\n🤖 Testing Selenium for: {url}")
    
    try:
        result = scrape_with_selenium(url, debug_html=True)
        if result and result != "No recipe content found":
            print(f"✅ Selenium: Successfully extracted content")
            print(f"   Content length: {len(result)} characters")
            return {
                'status': 'success',
                'content_length': len(result),
                'content_preview': result[:200] + "..." if len(result) > 200 else result
            }
        else:
            print(f"⚠️  Selenium: No recipe content found")
            return {
                'status': 'no_content',
                'content_length': 0
            }
            
    except Exception as e:
        print(f"❌ Selenium failed: {str(e)}")
        return {
            'status': 'failed',
            'error': str(e)
        }

def test_full_scraping(url: str) -> dict:
    """Test the full scraping pipeline."""
    print(f"\n🎯 Testing full scraping pipeline for: {url}")
    
    try:
        result = scrape_recipe_page(url, debug=True)
        
        if result.startswith("Error scraping recipe:"):
            print(f"❌ Full scraping failed: {result}")
            return {
                'status': 'failed',
                'error': result
            }
        elif result == "No recipe content found":
            print(f"⚠️  Full scraping: No recipe content found")
            return {
                'status': 'no_content',
                'content_length': 0
            }
        else:
            print(f"✅ Full scraping: Successfully extracted content")
            print(f"   Content length: {len(result)} characters")
            print(f"   Content preview: {result[:300]}...")
            return {
                'status': 'success',
                'content_length': len(result),
                'content_preview': result[:300] + "..." if len(result) > 300 else result
            }
            
    except Exception as e:
        print(f"❌ Full scraping failed: {str(e)}")
        return {
            'status': 'failed',
            'error': str(e)
        }

def analyze_website(url: str) -> dict:
    """Analyze a website to understand its structure and potential blocking."""
    print(f"\n📊 Analyzing website: {url}")
    
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    
    print(f"Domain: {domain}")
    print(f"Path: {parsed_url.path}")
    print(f"Scheme: {parsed_url.scheme}")
    
    # Test different approaches
    results = {
        'url': url,
        'domain': domain,
        'basic_request': test_basic_request(url),
        'cloudscraper': test_cloudscraper(url),
        'selenium': test_selenium(url),
        'full_scraping': test_full_scraping(url)
    }
    
    return results

def generate_report(results: dict) -> str:
    """Generate a detailed report of the test results."""
    report = []
    report.append("=" * 60)
    report.append("RECIPE WEBSITE SCRAPING ANALYSIS REPORT")
    report.append("=" * 60)
    report.append(f"URL: {results['url']}")
    report.append(f"Domain: {results['domain']}")
    report.append("")
    
    # Basic request results
    basic = results['basic_request']
    report.append("🔍 BASIC HTTP REQUEST:")
    if basic['status'] == 'success':
        report.append(f"   ✅ Status: {basic['status_code']}")
        report.append(f"   📏 Content Length: {basic['content_length']} bytes")
        report.append(f"   📄 Content Type: {basic['content_type']}")
    else:
        report.append(f"   ❌ Failed: {basic['error']}")
    
    # Cloudscraper results
    cloud = results['cloudscraper']
    report.append("\n🌐 CLOUDSCRAPER:")
    if cloud['status'] == 'success':
        report.append(f"   ✅ Status: {cloud['status_code']}")
        report.append(f"   📏 Content Length: {cloud['content_length']} bytes")
    else:
        report.append(f"   ❌ Failed: {cloud['error']}")
    
    # Selenium results
    selenium = results['selenium']
    report.append("\n🤖 SELENIUM:")
    if selenium['status'] == 'success':
        report.append(f"   ✅ Success: {selenium['content_length']} characters")
        report.append(f"   📝 Preview: {selenium['content_preview']}")
    elif selenium['status'] == 'no_content':
        report.append(f"   ⚠️  No recipe content found")
    else:
        report.append(f"   ❌ Failed: {selenium['error']}")
    
    # Full scraping results
    full = results['full_scraping']
    report.append("\n🎯 FULL SCRAPING PIPELINE:")
    if full['status'] == 'success':
        report.append(f"   ✅ Success: {full['content_length']} characters")
        report.append(f"   📝 Preview: {full['content_preview']}")
    elif full['status'] == 'no_content':
        report.append(f"   ⚠️  No recipe content found")
    else:
        report.append(f"   ❌ Failed: {full['error']}")
    
    # Recommendations
    report.append("\n" + "=" * 60)
    report.append("RECOMMENDATIONS:")
    report.append("=" * 60)
    
    if basic['status'] == 'failed':
        report.append("❌ Site is completely blocked or unreachable")
        report.append("   → Check if the URL is correct")
        report.append("   → Try accessing the site manually in a browser")
    elif cloud['status'] == 'success' and full['status'] == 'success':
        report.append("✅ Site is working well with current setup")
        report.append("   → No changes needed")
    elif cloud['status'] == 'success' and full['status'] != 'success':
        report.append("⚠️  Site is accessible but recipe parsing needs improvement")
        report.append("   → Check recipe content selectors")
        report.append("   → May need custom parsing for this site")
    elif selenium['status'] == 'success' and full['status'] != 'success':
        report.append("🤖 Selenium works but cloudscraper doesn't")
        report.append("   → Site has anti-bot protection")
        report.append("   → Consider using Selenium in production")
    else:
        report.append("❌ Site has strong anti-bot protection")
        report.append("   → May need to implement additional bypass methods")
        report.append("   → Consider using a proxy service")
    
    return "\n".join(report)

def main():
    """Main function to run the testing script."""
    if len(sys.argv) < 2:
        print("Usage: python test_scraping.py <recipe_url>")
        print("Example: python test_scraping.py https://www.allrecipes.com/recipe/12345")
        print("         python test_scraping.py https://www.maangchi.com/recipe/kimchi")
        sys.exit(1)
    
    url = sys.argv[1]
    
    print("🧪 RECIPE WEBSITE SCRAPING TESTER")
    print("=" * 50)
    print(f"Testing URL: {url}")
    print("=" * 50)
    
    # Run the analysis
    results = analyze_website(url)
    
    # Generate and print report
    report = generate_report(results)
    print("\n" + report)
    
    # Save results to file
    timestamp = int(time.time())
    filename = f"scraping_test_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📁 Detailed results saved to: {filename}")

if __name__ == "__main__":
    main()
