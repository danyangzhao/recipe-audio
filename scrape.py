# scrape.py
import requests
from bs4 import BeautifulSoup
import time
import json
import re
from typing import Optional, Dict, Any
from urllib.parse import urlparse
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

def scrape_recipe_page(url: str, max_retries: int = 3) -> str:
    """
    Scrapes a recipe webpage and returns the raw text content.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'DNT': '1',
    }

    for attempt in range(max_retries):
        try:
            # Add delay to respect rate limits
            time.sleep(2 * (attempt + 1))  # Exponential backoff
            
            logger.info(f"Attempting to scrape {url} (attempt {attempt + 1}/{max_retries})")
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            # Print response info for debugging
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Content length: {len(response.text)}")

            soup = BeautifulSoup(response.text, "html.parser")

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
    
    if len(sys.argv) != 2:
        print("Usage: python scrape.py <recipe_url>")
        print("Example: python scrape.py https://example.com/recipe")
        sys.exit(1)
        
    url = sys.argv[1]
    try:
        result = scrape_recipe_page(url)
        print("Successfully scraped recipe:")
        print("-" * 50)
        print(result)
        print("-" * 50)
    except Exception as e:
        print(f"Error scraping recipe: {str(e)}")
        sys.exit(1)
