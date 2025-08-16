# Recipe Website Scraping Troubleshooting Guide

## Quick Start: Testing Websites Locally

### 1. Basic Testing
```bash
# Test a single website
python test_scraping.py https://www.allrecipes.com/recipe/12345

# Test with debug output
python scrape.py https://www.allrecipes.com/recipe/12345 --debug

# Test the enhanced scraper
python enhanced_scraping.py https://www.allrecipes.com/recipe/12345
```

### 2. Test Multiple Websites
```bash
# Create a test file with URLs
echo "https://www.allrecipes.com/recipe/12345
https://www.foodnetwork.com/recipes/recipe-12345
https://www.maangchi.com/recipe/kimchi" > test_urls.txt

# Test all URLs
while read url; do
    echo "Testing: $url"
    python test_scraping.py "$url"
    echo "---"
    sleep 2
done < test_urls.txt
```

## Common Issues and Solutions

### 🔴 Issue: "Error scraping recipe: 403 Forbidden"
**Cause**: Website is blocking automated requests

**Solutions**:
1. **Use the enhanced scraper**:
   ```python
   from enhanced_scraping import scrape_recipe_page_enhanced
   result = scrape_recipe_page_enhanced(url)
   ```

2. **Install Selenium for local testing**:
   ```bash
   pip install undetected-chromedriver selenium
   ```

3. **Add more delays**:
   ```python
   # In scrape.py, increase delays
   time.sleep(random.uniform(3, 7))  # Instead of 1-3 seconds
   ```

### 🔴 Issue: "No recipe content found"
**Cause**: Website structure changed or selectors are outdated

**Solutions**:
1. **Use the enhanced scraper with site-specific selectors**
2. **Debug the HTML structure**:
   ```bash
   python test_scraping.py "URL" --debug
   ```
3. **Check if the site uses structured data (JSON-LD)**

### 🔴 Issue: "Connection timeout"
**Cause**: Network issues or rate limiting

**Solutions**:
1. **Increase timeout values**:
   ```python
   response = scraper.get(url, timeout=60)  # Increase from 30
   ```
2. **Add more retries**:
   ```python
   result = scrape_recipe_page(url, max_retries=5)
   ```

## Site-Specific Solutions

### AllRecipes.com
**Common Issues**: Rate limiting, dynamic content
**Solutions**:
- Use longer delays between requests
- The enhanced scraper has specific selectors for AllRecipes

### FoodNetwork.com
**Common Issues**: Anti-bot protection
**Solutions**:
- Use Selenium locally
- The enhanced scraper includes Food Network specific selectors

### Maangchi.com
**Common Issues**: Korean content, different structure
**Solutions**:
- The enhanced scraper has Maangchi-specific selectors
- Check for Korean character encoding issues

### Epicurious.com
**Common Issues**: Paywall detection
**Solutions**:
- Use rotating user agents
- Add referer headers

## Advanced Troubleshooting

### 1. Check Website Accessibility
```bash
# Test if the site is reachable
curl -I "https://example.com/recipe"
curl -A "Mozilla/5.0..." "https://example.com/recipe"
```

### 2. Analyze HTML Structure
```bash
# Save HTML for analysis
python -c "
import requests
from bs4 import BeautifulSoup
response = requests.get('URL', headers={'User-Agent': 'Mozilla/5.0...'})
with open('debug.html', 'w') as f:
    f.write(response.text)
"
```

### 3. Test Different User Agents
```python
user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0'
]
```

## Production Deployment Considerations

### Heroku Limitations
- **Selenium won't work** on Heroku (no Chrome)
- **Use cloudscraper** as primary method
- **Add more delays** to respect rate limits

### Rate Limiting
```python
# Add delays between requests
import time
import random

def scrape_with_delays(url):
    time.sleep(random.uniform(2, 5))  # Random delay
    # ... scraping code
```

### Proxy Services (Optional)
For heavily blocked sites, consider:
- **Bright Data** (formerly Luminati)
- **SmartProxy**
- **Oxylabs**

## Monitoring and Debugging

### 1. Enable Detailed Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 2. Track Success Rates
```python
# Add to your scraping function
success_count = 0
total_count = 0

def track_scraping_success(url, success):
    global success_count, total_count
    total_count += 1
    if success:
        success_count += 1
    
    print(f"Success rate: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
```

### 3. Save Failed URLs
```python
def log_failed_url(url, error):
    with open('failed_urls.txt', 'a') as f:
        f.write(f"{url}\t{error}\n")
```

## Quick Fixes for Common Problems

### Problem: All sites failing
**Quick Fix**: Update your scraping method
```python
# Replace in app.py
from enhanced_scraping import scrape_recipe_page_enhanced
raw_text = scrape_recipe_page_enhanced(recipe_url)
```

### Problem: Specific site failing
**Quick Fix**: Add site-specific handling
```python
# In enhanced_scraping.py, add new site config
'sitename.com': {
    'selectors': {
        'title': ['h1.recipe-title', 'h1'],
        'ingredients': ['.ingredients li'],
        'instructions': ['.instructions li']
    },
    'wait_time': 3
}
```

### Problem: Rate limiting
**Quick Fix**: Increase delays
```python
# In scrape.py
time.sleep(random.uniform(5, 10))  # Longer delays
```

## Testing Checklist

Before deploying changes:

- [ ] Test with 5+ different recipe sites
- [ ] Verify both simple and complex recipes work
- [ ] Check that audio generation still works
- [ ] Test on both local and production environments
- [ ] Monitor success rates for 24 hours
- [ ] Check for any new error patterns

## Emergency Fallback

If all scraping methods fail:

```python
def emergency_fallback(url):
    """Return a basic error message instead of failing completely."""
    return f"""
    Title: Recipe from {url}
    Description: Unable to automatically parse this recipe. Please try a different recipe URL or contact support.
    Ingredients: []
    Instructions: []
    """
```

## Getting Help

If you're still having issues:

1. **Run the test script** and share the output
2. **Check the debug HTML** for the failing site
3. **Try the enhanced scraper** first
4. **Consider the site's robots.txt** and terms of service
5. **Test manually** in a browser to see if the site is accessible

Remember: Some websites actively block scraping and may require manual intervention or different approaches.
