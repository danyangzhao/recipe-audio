# scrape.py
import requests
from bs4 import BeautifulSoup
import time
import json
import re
from typing import Optional, Dict, Any
from urllib.parse import urlparse
import logging
import random
from fake_useragent import UserAgent
import cloudscraper
import brotli
import gzip
import io
import os

# Try to import Selenium dependencies - they may not be available on Heroku
try:
    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    logging.warning("Selenium dependencies not available - will use cloudscraper only")

# Detect if running on Heroku or in a production environment
IS_HEROKU = os.environ.get('DYNO') is not None
IS_PRODUCTION = os.environ.get('PYTHON_ENV') == 'production' or IS_HEROKU

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_random_headers() -> Dict[str, str]:
    """
    Generate random headers to mimic a real browser.
    """
    try:
        ua = UserAgent()
        user_agent = ua.random
    except:
        # Fallback user agents if fake_useragent fails
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15'
        ]
        user_agent = random.choice(user_agents)

    return {
        'User-Agent': user_agent,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9,ko;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'DNT': '1',
        'Pragma': 'no-cache',
    }

def get_structured_data(soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
    """
    Extract structured data (JSON-LD) from the page if available.
    """
    try:
        script_tag = soup.find('script', {'type': 'application/ld+json'})
        if script_tag:
            data = json.loads(script_tag.string)
            if isinstance(data, list):
                # Find the recipe object in the list
                for item in data:
                    if isinstance(item, dict) and item.get('@type') == 'Recipe':
                        return item
            elif isinstance(data, dict) and data.get('@type') == 'Recipe':
                return data
    except Exception as e:
        logger.warning(f"Error parsing structured data: {str(e)}")
    return None

def clean_text(text: str) -> str:
    """
    Clean and normalize text content.
    """
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove special characters but keep Korean characters
    text = re.sub(r'[^\w\s\u3131-\uD7A3\uAC00-\uD7A3]', ' ', text)
    return text.strip()

def extract_recipe_content(soup: BeautifulSoup, url: str) -> str:
    """
    Extract recipe content using multiple methods.
    """
    content_parts = []
    
    # Try to get structured data first
    structured_data = get_structured_data(soup)
    if structured_data:
        logger.info("Found structured data")
        if 'name' in structured_data:
            content_parts.append(f"Title: {structured_data['name']}\n")
        if 'description' in structured_data:
            content_parts.append(f"Description: {structured_data['description']}\n")
        if 'recipeIngredient' in structured_data:
            content_parts.append("Ingredients:\n" + "\n".join(f"- {ing}" for ing in structured_data['recipeIngredient']))
        if 'recipeInstructions' in structured_data:
            instructions = []
            for step in structured_data['recipeInstructions']:
                if isinstance(step, dict) and 'text' in step:
                    instructions.append(step['text'])
                elif isinstance(step, str):
                    instructions.append(step)
            content_parts.append("Instructions:\n" + "\n".join(f"{i+1}. {step}" for i, step in enumerate(instructions)))
        return "\n\n".join(content_parts)

    # If no structured data, try specific selectors for Maangchi
    if 'maangchi.com' in url:
        logger.info("Using Maangchi-specific selectors")
        # Try to find the main content area
        main_content = (
            soup.find('div', class_='entry-content') or
            soup.find('div', class_='recipe-content') or
            soup.find('article', class_='post')
        )
        
        if main_content:
            # Get title
            title = (
                soup.find('h1', class_=['recipe-title', 'entry-title']) or
                soup.find('h1')
            )
            if title:
                content_parts.append(f"Title: {clean_text(title.get_text())}\n")
            
            # Get ingredients
            ingredients = main_content.find(['div', 'ul'], class_=['ingredients', 'recipe-ingredients'])
            if ingredients:
                content_parts.append("Ingredients:\n" + clean_text(ingredients.get_text(separator="\n")))
            
            # Get instructions
            instructions = main_content.find(['div', 'ol'], class_=['instructions', 'directions', 'steps'])
            if instructions:
                content_parts.append("Instructions:\n" + clean_text(instructions.get_text(separator="\n")))
            
            if content_parts:
                return "\n\n".join(content_parts)

    # Fallback to general recipe selectors
    logger.info("Using general recipe selectors")
    recipe_content = (
        soup.find('div', {'id': ['recipe-single', 'recipe-container', 'recipe-card', 'recipe']}) or
        soup.find('div', class_=['recipe-content', 'recipe-card', 'recipe-box', 'entry-content']) or
        soup.find('article', class_=['recipe', 'post']) or
        soup.find('main') or
        soup.find('article')
    )

    if recipe_content:
        # Get title
        title = (
            soup.find('h1', class_=['recipe-title', 'entry-title']) or
            soup.find('h1', {'id': 'recipe-title'}) or
            soup.find('h1')
        )
        if title:
            content_parts.append(f"Title: {clean_text(title.get_text())}\n")

        # Extract content
        if recipe_content:
            # Try to find structured sections
            ingredients = recipe_content.find(['div', 'ul'], class_=['ingredients', 'recipe-ingredients']) or \
                        recipe_content.find(['div', 'ul'], string=lambda x: x and 'ingredients' in x.lower())
            
            instructions = recipe_content.find(['div', 'ol'], class_=['instructions', 'directions', 'steps']) or \
                         recipe_content.find(['div', 'ol'], string=lambda x: x and any(word in x.lower() for word in ['instructions', 'directions', 'steps']))

            # Add ingredients
            if ingredients:
                content_parts.append("Ingredients:\n" + clean_text(ingredients.get_text(separator="\n")))
            
            # Add instructions
            if instructions:
                content_parts.append("Instructions:\n" + clean_text(instructions.get_text(separator="\n")))

            # If no structured content found, use all content
            if not (ingredients or instructions):
                content_parts.append(clean_text(recipe_content.get_text(separator="\n")))

    return "\n\n".join(content_parts) if content_parts else "No recipe content found"

def decode_response_content(response) -> str:
    """
    Properly decode response content handling various compression formats.
    """
    try:
        # Get the raw content
        content = response.content
        
        # Check content encoding from headers
        encoding = response.headers.get('content-encoding', '').lower()
        
        if encoding == 'br' or encoding == 'brotli':
            # Brotli decompression
            try:
                decompressed = brotli.decompress(content)
                content = decompressed
            except Exception as e:
                logger.warning(f"Failed to decompress brotli content: {e}")
        elif encoding == 'gzip':
            # Gzip decompression
            try:
                decompressed = gzip.decompress(content)
                content = decompressed
            except Exception as e:
                logger.warning(f"Failed to decompress gzip content: {e}")
        elif encoding == 'deflate':
            # Deflate decompression
            try:
                import zlib
                decompressed = zlib.decompress(content)
                content = decompressed
            except Exception as e:
                logger.warning(f"Failed to decompress deflate content: {e}")
        
        # Decode bytes to string
        if isinstance(content, bytes):
            # Try to detect encoding
            charset = None
            content_type = response.headers.get('content-type', '')
            if 'charset=' in content_type:
                charset = content_type.split('charset=')[1].split(';')[0].strip()
            
            if not charset:
                # Try to detect from content
                try:
                    import chardet
                    detected = chardet.detect(content[:1000])
                    charset = detected.get('encoding', 'utf-8')
                except ImportError:
                    logger.warning("chardet not available, using utf-8")
                    charset = 'utf-8'
                except Exception:
                    charset = 'utf-8'
            
            try:
                return content.decode(charset)
            except:
                return content.decode('utf-8', errors='ignore')
        
        return str(content)
    except Exception as e:
        logger.error(f"Error decoding response content: {e}")
        # Fallback to response.text
        return response.text

def scrape_with_selenium(url: str, debug_html: bool = False) -> str:
    """
    Scrape using Selenium with undetected-chromedriver to bypass Cloudflare.
    Returns empty string if Selenium is not available or on Heroku.
    """
    # Skip Selenium on Heroku or when not available
    if IS_HEROKU or IS_PRODUCTION or not SELENIUM_AVAILABLE:
        logger.info("Skipping Selenium (not available or running on Heroku)")
        return ""
    
    try:
        options = uc.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        driver = uc.Chrome(options=options)
        driver.get(url)
        
        # Wait for the content to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Get the page source after JavaScript execution
        html = driver.page_source
        driver.quit()
        
        if debug_html:
            # Print relevant parts of the HTML for debugging
            soup = BeautifulSoup(html, "html.parser")
            
            # Remove script and style tags for cleaner output
            for element in soup.find_all(['script', 'style']):
                element.decompose()
            
            print("=== DEBUG: HTML STRUCTURE ===")
            print("Page title:", soup.find('title').get_text() if soup.find('title') else "No title found")
            
            # Look for main content containers
            print("\n=== MAIN CONTENT CONTAINERS ===")
            main_containers = soup.find_all(['main', 'article', 'div'], class_=re.compile(r'(content|recipe|post|entry)', re.I))
            for i, container in enumerate(main_containers[:3]):  # Show first 3
                print(f"\nContainer {i+1}: {container.name} with class='{container.get('class')}'")
                print(f"ID: {container.get('id')}")
                # Show first 200 chars of text content
                text = container.get_text()[:200].strip()
                print(f"Text preview: {text}...")
            
            # Look for headings
            print("\n=== HEADINGS ===")
            headings = soup.find_all(['h1', 'h2', 'h3'])
            for h in headings[:5]:  # Show first 5 headings
                print(f"{h.name}: {h.get_text().strip()[:100]}")
                print(f"  Classes: {h.get('class')}")
                print(f"  ID: {h.get('id')}")
            
            # Look for lists (potential ingredients)
            print("\n=== LISTS (potential ingredients/instructions) ===")
            lists = soup.find_all(['ul', 'ol'])
            for i, lst in enumerate(lists[:3]):  # Show first 3 lists
                print(f"\nList {i+1}: {lst.name} with class='{lst.get('class')}'")
                items = lst.find_all('li')[:3]  # Show first 3 items
                for j, item in enumerate(items):
                    print(f"  Item {j+1}: {item.get_text().strip()[:50]}...")
            
            print("\n=== END DEBUG ===\n")
        
        soup = BeautifulSoup(html, "html.parser")
        return extract_recipe_content(soup, url)
    except Exception as e:
        logger.error(f"Error with Selenium scraping: {str(e)}")
        return ""

def scrape_recipe_page(url: str, max_retries: int = 3, debug: bool = False) -> str:
    """
    Scrapes a recipe webpage and returns the raw text content.
    """
    # Try with Selenium first (only if available and not on Heroku)
    if SELENIUM_AVAILABLE and not IS_HEROKU and not IS_PRODUCTION:
        logger.info("Attempting to scrape with Selenium")
        result = scrape_with_selenium(url, debug_html=debug)
        if result and result != "No recipe content found":
            return result
        else:
            logger.info("Selenium didn't return content, falling back to cloudscraper")
    else:
        logger.info("Using cloudscraper only (Selenium not available or on Heroku)")
    
    # Use cloudscraper (this works well on Heroku)
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'mobile': False
        },
        delay=10,
        debug=False
    )
    
    # Configure session to handle compression properly
    scraper.headers.update({
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'
    })
    
    for attempt in range(max_retries):
        try:
            # Add delay to respect rate limits with jitter
            delay = 2 * (attempt + 1) + random.uniform(0, 1)
            time.sleep(delay)
            
            logger.info(f"Attempting to scrape {url} with cloudscraper (attempt {attempt + 1}/{max_retries})")
            
            # Get fresh headers for each attempt
            headers = get_random_headers()
            
            # Add referer for the domain
            parsed_url = urlparse(url)
            headers['Referer'] = f"{parsed_url.scheme}://{parsed_url.netloc}/"
            
            response = scraper.get(url, headers=headers, timeout=30, stream=False)
            response.raise_for_status()
            
            # Properly decode the content
            html_content = decode_response_content(response)
            
            # Print response info for debugging
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Content length: {len(html_content)}")
            logger.info(f"Content encoding: {response.headers.get('content-encoding', 'none')}")
            if debug and attempt == 0:
                logger.info(f"Response headers: {dict(response.headers)}")

            soup = BeautifulSoup(html_content, "html.parser")

            # Debug: Print HTML structure from cloudscraper
            if debug and attempt == 0:  # Only debug on first attempt
                print("=== DEBUG: CLOUDSCRAPER HTML STRUCTURE ===")
                print("Page title:", soup.find('title').get_text() if soup.find('title') else "No title found")
                
                # Print first 1000 characters of raw HTML
                print("\n=== RAW HTML PREVIEW ===")
                print(html_content[:1000])
                print("...")
                print(html_content[-500:])  # Last 500 characters
                print("\n=== END RAW HTML ===")
                
                # Look for main content containers
                print("\n=== MAIN CONTENT CONTAINERS ===")
                main_containers = soup.find_all(['main', 'article', 'div'], class_=re.compile(r'(content|recipe|post|entry)', re.I))
                for i, container in enumerate(main_containers[:5]):  # Show first 5
                    print(f"\nContainer {i+1}: {container.name} with class='{container.get('class')}'")
                    print(f"ID: {container.get('id')}")
                    # Show first 200 chars of text content
                    text = container.get_text()[:200].strip()
                    print(f"Text preview: {text}...")
                
                # Look for headings
                print("\n=== HEADINGS ===")
                headings = soup.find_all(['h1', 'h2', 'h3'])
                for h in headings[:10]:  # Show first 10 headings
                    print(f"{h.name}: {h.get_text().strip()[:100]}")
                    print(f"  Classes: {h.get('class')}")
                    print(f"  ID: {h.get('id')}")
                
                # Look for lists (potential ingredients)
                print("\n=== LISTS (potential ingredients/instructions) ===")
                lists = soup.find_all(['ul', 'ol'])
                for i, lst in enumerate(lists[:5]):  # Show first 5 lists
                    print(f"\nList {i+1}: {lst.name} with class='{lst.get('class')}'")
                    print(f"ID: {lst.get('id')}")
                    items = lst.find_all('li')[:3]  # Show first 3 items
                    for j, item in enumerate(items):
                        print(f"  Item {j+1}: {item.get_text().strip()[:100]}...")
                
                # Look for specific divs that might contain recipe content
                print("\n=== POTENTIAL RECIPE CONTAINERS ===")
                recipe_divs = soup.find_all('div', class_=re.compile(r'recipe|ingredients|directions|instructions', re.I))
                for i, div in enumerate(recipe_divs[:5]):
                    print(f"\nRecipe Div {i+1}: class='{div.get('class')}'")
                    print(f"ID: {div.get('id')}")
                    text = div.get_text()[:200].strip()
                    print(f"Text preview: {text}...")
                
                print("\n=== END CLOUDSCRAPER DEBUG ===\n")

            # Remove unwanted elements
            for element in soup.find_all(['script', 'style', 'iframe', 'noscript']):
                element.decompose()

            # Extract recipe content
            result = extract_recipe_content(soup, url)
            
            if result and result != "No recipe content found":
                logger.info("Successfully extracted recipe content")
                return result
            else:
                logger.warning("No recipe content found, retrying...")
                continue

        except requests.exceptions.RequestException as e:
            logger.error(f"Request error on attempt {attempt + 1}: {str(e)}")
            if attempt == max_retries - 1:
                return f"Error scraping recipe: {str(e)}"
            continue
        except Exception as e:
            logger.error(f"Unexpected error on attempt {attempt + 1}: {str(e)}")
            if attempt == max_retries - 1:
                return f"Error scraping recipe: {str(e)}"
            continue

    return "Failed to extract recipe content after all attempts"

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python scrape.py <recipe_url> [--debug]")
        print("Example: python scrape.py https://example.com/recipe")
        print("         python scrape.py https://example.com/recipe --debug")
        sys.exit(1)
        
    url = sys.argv[1]
    debug_mode = '--debug' in sys.argv
    
    try:
        result = scrape_recipe_page(url, debug=debug_mode)
        print("Successfully scraped recipe:")
        print("-" * 50)
        print(result)
        print("-" * 50)
    except Exception as e:
        print(f"Error scraping recipe: {str(e)}")
        sys.exit(1)
