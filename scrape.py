# scrape.py
import requests
from bs4 import BeautifulSoup

def scrape_recipe_page(url: str) -> str:
    """
    Scrapes a recipe webpage and returns the raw text content.
    Includes browser-like headers to avoid being blocked.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }

    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()  # Raise if there's an HTTP error

    soup = BeautifulSoup(response.text, "html.parser")

    # Look for the main recipe content
    recipe_content = soup.find('div', class_='entry-content')
    if recipe_content:
        # Remove any comment sections
        comments = recipe_content.find_all(['div', 'section'], class_=['comments', 'comment-list'])
        for comment in comments:
            comment.decompose()
            
        # Remove any sidebar content
        sidebar = recipe_content.find_all('div', class_='sidebar')
        for side in sidebar:
            side.decompose()
            
        return recipe_content.get_text(separator="\n").strip()
    
    # Fallback to main content
    main_content = soup.find('main') or soup.find('article')
    if main_content:
        # Remove comments section if present
        comments = main_content.find_all(['div', 'section'], class_=['comments', 'comment-list'])
        for comment in comments:
            comment.decompose()
        return main_content.get_text(separator="\n").strip()

    # If all else fails, return full page text
    return soup.get_text(separator="\n").strip()

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
