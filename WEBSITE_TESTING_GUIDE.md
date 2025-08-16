# Website Testing and Troubleshooting Guide

## 🚀 Quick Start: Test Your Recipe Websites

### 1. Quick Test (Recommended First Step)
```bash
# Test a single website quickly
python quick_test.py https://www.allrecipes.com/recipe/12345
```

### 2. Detailed Analysis
```bash
# Get comprehensive analysis of a website
python test_scraping.py https://www.allrecipes.com/recipe/12345
```

### 3. Debug Mode
```bash
# See detailed HTML structure and debugging info
python scrape.py https://www.allrecipes.com/recipe/12345 --debug
```

## 📋 What I've Created for You

### New Files Added:
1. **`test_scraping.py`** - Comprehensive testing script with detailed analysis
2. **`enhanced_scraping.py`** - Advanced scraper with site-specific parsers
3. **`quick_test.py`** - Simple, fast testing for single URLs
4. **`SCRAPING_TROUBLESHOOTING.md`** - Detailed troubleshooting guide

### Updated Files:
1. **`app.py`** - Now uses enhanced scraper as fallback
2. **`process_recipe.py`** - Improved with JSON response format
3. **`requirements.txt`** - Updated OpenAI SDK version

## 🔧 How to Test Different Websites

### Step 1: Quick Test
```bash
# Test if a website works at all
python quick_test.py "YOUR_RECIPE_URL"
```

### Step 2: If Quick Test Fails
```bash
# Get detailed analysis
python test_scraping.py "YOUR_RECIPE_URL"
```

### Step 3: Check the Results
The test scripts will tell you:
- ✅ Which scraping methods work
- ❌ Which methods fail and why
- 📊 Success rates and recommendations
- 🔍 Detailed HTML structure analysis

## 🎯 Common Scenarios and Solutions

### Scenario 1: "Both scrapers failed"
**What it means**: The website has strong anti-bot protection
**Solutions**:
1. Try a different recipe URL from the same site
2. Check if the site is accessible in a browser
3. The site may require manual intervention

### Scenario 2: "Only enhanced scraper works"
**What it means**: The site has basic anti-bot protection
**Solutions**:
1. Your app will automatically use the enhanced scraper
2. No action needed - it's working as designed

### Scenario 3: "Only original scraper works"
**What it means**: The site works fine with basic scraping
**Solutions**:
1. No action needed - your app will use the original scraper
2. The enhanced scraper is just a backup

### Scenario 4: "Both scrapers work"
**What it means**: Perfect! The site is easily accessible
**Solutions**:
1. Your app will use whichever method works first
2. No action needed

## 🛠️ Troubleshooting Specific Issues

### Issue: "403 Forbidden"
**Quick Fix**: The enhanced scraper should handle this automatically
**Manual Fix**: 
```python
# In scrape.py, increase delays
time.sleep(random.uniform(5, 10))  # Longer delays
```

### Issue: "No recipe content found"
**Quick Fix**: The enhanced scraper has better content extraction
**Manual Fix**: Check the debug output to see what HTML is being received

### Issue: "Connection timeout"
**Quick Fix**: Increase timeout values
```python
# In enhanced_scraping.py
response = self.scraper.get(url, headers=headers, timeout=60)  # Increase from 30
```

## 📊 Testing Multiple Websites

### Batch Testing
```bash
# Create a file with URLs to test
echo "https://www.allrecipes.com/recipe/12345
https://www.foodnetwork.com/recipes/recipe-12345
https://www.maangchi.com/recipe/kimchi" > test_urls.txt

# Test all URLs
while read url; do
    echo "Testing: $url"
    python quick_test.py "$url"
    echo "---"
    sleep 2
done < test_urls.txt
```

### Monitor Success Rates
The test scripts will show you:
- How many sites work with each method
- Which sites are problematic
- Recommendations for each site

## 🚀 Production Deployment

### What Works on Heroku:
- ✅ Cloudscraper (primary method)
- ✅ Regular requests (fallback)
- ❌ Selenium (won't work on Heroku)

### What I've Done:
1. **Added fallback system**: If original scraper fails, enhanced scraper tries
2. **Improved error handling**: Better error messages and recovery
3. **Site-specific parsers**: Better content extraction for popular sites
4. **Rate limiting**: Respectful delays between requests

## 📈 Monitoring Your App

### Check Success Rates
Your app now logs when it falls back to the enhanced scraper:
```
Original scraper failed, trying enhanced scraper for: https://example.com/recipe
```

### Track Performance
Monitor these metrics:
- How often the enhanced scraper is used
- Which sites consistently fail
- Success rates over time

## 🔍 Advanced Debugging

### If You Need More Details:
```bash
# Get full HTML analysis
python test_scraping.py "URL" > debug_output.txt

# Check what the scraper sees
python scrape.py "URL" --debug
```

### Common Debugging Steps:
1. **Test manually**: Can you access the site in a browser?
2. **Check robots.txt**: Is the site blocking scrapers?
3. **Try different URLs**: Some recipes might be more accessible than others
4. **Check site structure**: Has the website changed recently?

## 🎯 Next Steps

### Immediate Actions:
1. **Test your problematic URLs** with the quick test script
2. **Deploy the updated app** - it now has better fallback handling
3. **Monitor the logs** to see which sites work and which don't

### If You Still Have Issues:
1. **Run the detailed test script** and share the output
2. **Check the troubleshooting guide** for specific solutions
3. **Consider the site's terms of service** - some sites actively block scraping

## 💡 Pro Tips

1. **Start with popular sites**: AllRecipes, Food Network, Epicurious usually work well
2. **Test during off-peak hours**: Some sites have different rate limits
3. **Use the enhanced scraper**: It has better success rates for problematic sites
4. **Monitor your logs**: The app will tell you when it's using fallback methods

## 🆘 Getting Help

If you're still having issues:
1. Run `python test_scraping.py "URL"` and share the output
2. Check if the site is accessible in a browser
3. Look at the detailed troubleshooting guide
4. Consider if the site has changed its structure recently

Remember: The enhanced scraper should handle most common blocking issues automatically!
