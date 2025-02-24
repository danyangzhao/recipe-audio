# scrape.py
import requests
from bs4 import BeautifulSoup
import time

def scrape_recipe_page(url: str) -> str:
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

    try:
        # Add delay to respect rate limits
        time.sleep(2)
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Print response info for debugging
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {response.headers}")
        print(f"Content length: {len(response.text)}")

        soup = BeautifulSoup(response.text, "html.parser")

        # Debug print
        print(f"Initial HTML length: {len(str(soup))}")

        # Remove unwanted elements
        for element in soup.find_all(['script', 'style', 'iframe', 'noscript']):
            element.decompose()

        # Try multiple selectors specific to Maangchi and general recipe sites
        recipe_content = None
        
        # Specific to Maangchi
        recipe_content = (
            soup.find('div', class_='entry-content') or
            soup.find('div', class_='recipe-content') or
            soup.find('div', {'id': 'recipe'})
        )

        if not recipe_content:
            # General recipe selectors
            recipe_content = (
                soup.find('div', {'id': ['recipe-single', 'recipe-container', 'recipe-card', 'recipe']}) or
                soup.find('div', class_=['recipe-content', 'recipe-card', 'recipe-box', 'entry-content']) or
                soup.find('article', class_=['recipe', 'post']) or
                soup.find('main') or
                soup.find('article')
            )

        if not recipe_content:
            print("No recipe content found with standard selectors")
            # Fallback to body content
            recipe_content = soup.find('body')

        # Get title
        title = (
            soup.find('h1', class_=['recipe-title', 'entry-title']) or
            soup.find('h1', {'id': 'recipe-title'}) or
            soup.find('h1')
        )
        
        title_text = f"Title: {title.get_text().strip()}\n\n" if title else ""
        
        # Debug print
        print(f"Found title: {title_text}")

        # Extract content
        content_parts = []
        if title_text:
            content_parts.append(title_text)

        if recipe_content:
            # Try to find structured sections
            ingredients = recipe_content.find(['div', 'ul'], class_=['ingredients', 'recipe-ingredients']) or \
                        recipe_content.find(['div', 'ul'], string=lambda x: x and 'ingredients' in x.lower())
            
            instructions = recipe_content.find(['div', 'ol'], class_=['instructions', 'directions', 'steps']) or \
                         recipe_content.find(['div', 'ol'], string=lambda x: x and any(word in x.lower() for word in ['instructions', 'directions', 'steps']))

            # Add ingredients
            if ingredients:
                content_parts.append("Ingredients:\n" + ingredients.get_text(separator="\n").strip())
            
            # Add instructions
            if instructions:
                content_parts.append("Instructions:\n" + instructions.get_text(separator="\n").strip())

            # If no structured content found, use all content
            if not (ingredients or instructions):
                content_parts.append(recipe_content.get_text(separator="\n").strip())

        result = "\n\n".join(content_parts)
        
        # Debug print
        print(f"Final extracted content length: {len(result)}")
        print("First 200 characters of content:", result[:200])

        return result

    except Exception as e:
        print(f"Error scraping recipe: {str(e)}")
        return f"Error scraping recipe: {str(e)}"

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
