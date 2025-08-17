# enhanced_scraping.py
"""
Enhanced scraping module with better anti-blocking techniques and site-specific parsers.
This module provides more robust scraping capabilities for recipe websites.
"""

import requests
from bs4 import BeautifulSoup
import time
import json
import re
import random
import logging
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse
from fake_useragent import UserAgent
import cloudscraper
import brotli
import gzip
import io
import os

# Try to import Selenium dependencies
try:
	import undetected_chromedriver as uc
	from selenium.webdriver.common.by import By
	from selenium.webdriver.support.ui import WebDriverWait
	from selenium.webdriver.support import expected_conditions as EC
	from selenium.webdriver.chrome.options import Options
	SELENIUM_AVAILABLE = True
except ImportError:
	SELENIUM_AVAILABLE = False
	logging.warning("Selenium dependencies not available")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedRecipeScraper:
	"""Enhanced recipe scraper with multiple fallback methods and site-specific parsers."""
	
	def __init__(self):
		self.session = requests.Session()
		self.scraper = cloudscraper.create_scraper(
			browser={
				'browser': 'chrome',
				'platform': 'windows',
				'mobile': False
			},
			delay=10
		)
		
		# Rotate user agents
		self.user_agents = [
			'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
			'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
			'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
			'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
			'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
		]
		
		# Site-specific configurations
		self.site_configs = {
			'allrecipes.com': {
				'selectors': {
					'title': ['h1.recipe-title', 'h1.recipe-header__title', 'h1'],
					'ingredients': ['.ingredients-item-name', '.ingredients-list li', '.recipe-ingredients li'],
					'instructions': ['.instructions li', '.recipe-directions li', '.directions li']
				},
				'wait_time': 2
			},
			'foodnetwork.com': {
				'selectors': {
					'title': ['h1.o-AssetTitle__a-Headline', 'h1.recipe-title', 'h1'],
					'ingredients': ['.o-Ingredients__a-Ingredient', '.ingredients li', '.recipe-ingredients li'],
					'instructions': ['.o-Method__m-Step', '.directions li', '.recipe-directions li']
				},
				'wait_time': 3
			},
			'epicurious.com': {
				'selectors': {
					'title': ['h1.recipe-title', 'h1.title', 'h1'],
					'ingredients': ['.ingredients li', '.recipe-ingredients li'],
					'instructions': ['.instructions li', '.recipe-directions li']
				},
				'wait_time': 2
			},
			'maangchi.com': {
				'selectors': {
					'title': ['h1.recipe-title', 'h1.entry-title', 'h1'],
					'ingredients': ['.ingredients li', '.recipe-ingredients li', '.ingredients-list li'],
					'instructions': ['.instructions li', '.recipe-directions li', '.directions li']
				},
				'wait_time': 2
			},
			'seriouseats.com': {
				'selectors': {
					'title': ['h1.recipe-title', 'h1.title', 'h1'],
					'ingredients': ['.ingredients li', '.recipe-ingredients li'],
					'instructions': ['.instructions li', '.recipe-directions li']
				},
				'wait_time': 2
			}
		}
		# Add site-specific config for 10000recipe.com (Korean)
		self.site_configs['10000recipe.com'] = {
			'selectors': {
				'title': ['h3.view2_tit', 'h1.recipe-title', 'h1'],
				'ingredients': ['.ready_ingre3 li', '#divConfirmedMaterialArea li', '.cont_ingre li', '.ingre_list li', '.ingredient_list li'],
				'instructions': ['.view_step .media .media-body', '.view_step .step_text', '.view_step li']
			},
			'wait_time': 2
		}
	
	def get_random_headers(self, url: str) -> Dict[str, str]:
		"""Generate random headers with referer."""
		user_agent = random.choice(self.user_agents)
		parsed_url = urlparse(url)
		
		return {
			'User-Agent': user_agent,
			'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
			'Accept-Language': 'en-US,en;q=0.9',
			'Accept-Encoding': 'gzip, deflate, br',
			'Connection': 'keep-alive',
			'Upgrade-Insecure-Requests': '1',
			'Cache-Control': 'max-age=0',
			'Sec-Fetch-Dest': 'document',
			'Sec-Fetch-Mode': 'navigate',
			'Sec-Fetch-Site': 'none',
			'Sec-Fetch-User': '?1',
			'DNT': '1',
			'Referer': f"{parsed_url.scheme}://{parsed_url.netloc}/",
			'Pragma': 'no-cache',
		}
	
	def get_site_config(self, url: str) -> Dict[str, Any]:
		"""Get site-specific configuration based on domain."""
		domain = urlparse(url).netloc.lower()
		
		# Remove www. prefix
		if domain.startswith('www.'):
			domain = domain[4:]
		
		# Find matching site config
		for site_domain, config in self.site_configs.items():
			if site_domain in domain:
				return config
		
		# Default config
		return {
			'selectors': {
				'title': ['h1.recipe-title', 'h1.title', 'h1'],
				'ingredients': ['.ingredients li', '.recipe-ingredients li', '.ingredients-list li'],
				'instructions': ['.instructions li', '.recipe-directions li', '.directions li']
			},
			'wait_time': 2
		}
	
	def extract_with_selectors(self, soup: BeautifulSoup, selectors: List[str]) -> List[str]:
		"""Extract content using multiple CSS selectors."""
		for selector in selectors:
			elements = soup.select(selector)
			if elements:
				texts: List[str] = []
				for elem in elements:
					text = elem.get_text(" ", strip=True)
					text = re.sub(r'\s*구매\s*$', '', text)
					if text:
						texts.append(text)
				return texts
		return []
	
	def extract_structured_data(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
		"""Extract structured data (JSON-LD) from the page."""
		try:
			# Look for JSON-LD scripts
			scripts = soup.find_all('script', {'type': 'application/ld+json'})
			
			for script in scripts:
				try:
					if not script.string:
						continue
					data = json.loads(script.string)
					
					# Handle both single objects and arrays
					if isinstance(data, list):
						for item in data:
							if isinstance(item, dict):
								atype = item.get('@type')
								if atype == 'Recipe' or (isinstance(atype, list) and 'Recipe' in atype):
									return item
								if '@graph' in item and isinstance(item['@graph'], list):
									for g in item['@graph']:
										if isinstance(g, dict):
											gat = g.get('@type')
											if gat == 'Recipe' or (isinstance(gat, list) and 'Recipe' in gat):
												return g
					elif isinstance(data, dict):
						atype = data.get('@type')
						if atype == 'Recipe' or (isinstance(atype, list) and 'Recipe' in atype):
							return data
						if '@graph' in data and isinstance(data['@graph'], list):
							for g in data['@graph']:
								if isinstance(g, dict):
									gat = g.get('@type')
									if gat == 'Recipe' or (isinstance(gat, list) and 'Recipe' in gat):
										return g
						
				except json.JSONDecodeError:
					continue
			
		except Exception as e:
			logger.warning(f"Error parsing structured data: {str(e)}")
		
		return None
	
	def parse_structured_recipe(self, data: Dict[str, Any]) -> Dict[str, Any]:
		"""Parse structured recipe data into our format."""
		recipe = {
			'title': '',
			'ingredients': [],
			'instructions': [],
			'description': ''
		}
		
		# Extract title
		if 'name' in data:
			recipe['title'] = data['name']
		
		# Extract description
		if 'description' in data:
			recipe['description'] = data['description']
		
		# Extract ingredients
		if 'recipeIngredient' in data:
			recipe['ingredients'] = data['recipeIngredient']
		
		# Extract instructions
		if 'recipeInstructions' in data:
			instructions = data['recipeInstructions']
			if isinstance(instructions, list):
				for step in instructions:
					if isinstance(step, dict) and 'text' in step:
						recipe['instructions'].append(step['text'])
					elif isinstance(step, str):
						recipe['instructions'].append(step)
		
		return recipe
	
	def scrape_with_selenium(self, url: str) -> Optional[str]:
		"""Scrape using Selenium with undetected-chromedriver."""
		if not SELENIUM_AVAILABLE:
			return None
		
		try:
			options = uc.ChromeOptions()
			options.add_argument('--headless')
			options.add_argument('--no-sandbox')
			options.add_argument('--disable-dev-shm-usage')
			options.add_argument('--disable-blink-features=AutomationControlled')
			# Remove problematic experimental options for older Chrome versions
			# options.add_experimental_option("excludeSwitches", ["enable-automation"])
			# options.add_experimental_option('useAutomationExtension', False)
			
			driver = uc.Chrome(options=options)
			# Remove problematic script execution for older Chrome versions
			# driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
			
			# Get site config for wait time
			site_config = self.get_site_config(url)
			wait_time = site_config.get('wait_time', 2)
			
			driver.get(url)
			time.sleep(wait_time)  # Wait for content to load
			
			# Wait for body to be present
			WebDriverWait(driver, 10).until(
				EC.presence_of_element_located((By.TAG_NAME, "body"))
			)
			
			html = driver.page_source
			driver.quit()
			
			return html
			
		except Exception as e:
			logger.error(f"Selenium scraping failed: {str(e)}")
			return None
	
	def scrape_with_cloudscraper(self, url: str) -> Optional[str]:
		"""Scrape using cloudscraper."""
		try:
			headers = self.get_random_headers(url)
			
			# Add delay to respect rate limits
			time.sleep(random.uniform(1, 3))
			
			response = self.scraper.get(url, headers=headers, timeout=30)
			response.raise_for_status()
			
			return response.text
			
		except Exception as e:
			logger.error(f"Cloudscraper failed: {str(e)}")
			return None
	
	def scrape_with_requests(self, url: str) -> Optional[str]:
		"""Scrape using regular requests with rotating headers."""
		try:
			headers = self.get_random_headers(url)
			
			# Add delay to respect rate limits
			time.sleep(random.uniform(1, 2))
			
			response = self.session.get(url, headers=headers, timeout=15)
			response.raise_for_status()
			
			return response.text
			
		except Exception as e:
			logger.error(f"Regular requests failed: {str(e)}")
			return None
	
	def extract_recipe_content(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
		"""Extract recipe content using multiple methods."""
		# First try structured data
		structured_data = self.extract_structured_data(soup)
		if structured_data:
			logger.info("Found structured data")
			return self.parse_structured_recipe(structured_data)
		
		# Get site-specific configuration
		site_config = self.get_site_config(url)
		selectors = site_config['selectors']
		
		# Extract using site-specific selectors
		title = self.extract_with_selectors(soup, selectors['title'])
		ingredients = self.extract_with_selectors(soup, selectors['ingredients'])
		instructions = self.extract_with_selectors(soup, selectors['instructions'])
		
		# Fallback to general selectors if no content found
		if not title:
			title = self.extract_with_selectors(soup, ['h1', '.title', '.recipe-title'])
		
		if not ingredients:
			ingredients = self.extract_with_selectors(soup, ['ul li', 'ol li'])
		
		if not instructions:
			instructions = self.extract_with_selectors(soup, ['.instructions li', '.directions li', '.steps li', '.step_text'])
		
		return {
			'title': title[0] if title else 'Recipe',
			'ingredients': ingredients,
			'instructions': instructions,
			'description': ''
		}
	
	def scrape_recipe(self, url: str, max_retries: int = 3) -> Dict[str, Any]:
		"""Main scraping method with multiple fallback strategies."""
		logger.info(f"Scraping recipe from: {url}")
		
		# Try different scraping methods
		methods = [
			('selenium', self.scrape_with_selenium),
			('cloudscraper', self.scrape_with_cloudscraper),
			('requests', self.scrape_with_requests)
		]
		
		for method_name, method_func in methods:
			logger.info(f"Trying {method_name}...")
			
			for attempt in range(max_retries):
				try:
					html = method_func(url)
					
					if html:
						soup = BeautifulSoup(html, 'html.parser')
						
						# Remove unwanted elements
						for element in soup.find_all(['script', 'style', 'iframe', 'noscript']):
							element.decompose()
						
						# Extract recipe content
						recipe = self.extract_recipe_content(soup, url)
						
						if recipe['ingredients'] or recipe['instructions']:
							logger.info(f"Successfully extracted recipe using {method_name}")
							return {
								'success': True,
								'method': method_name,
								'recipe': recipe
							}
					
					# Add delay between retries
					if attempt < max_retries - 1:
						time.sleep(random.uniform(2, 5))
						
				except Exception as e:
					logger.error(f"{method_name} attempt {attempt + 1} failed: {str(e)}")
					if attempt < max_retries - 1:
						time.sleep(random.uniform(2, 5))
		
		# If all methods failed
		return {
			'success': False,
			'error': 'All scraping methods failed',
			'recipe': {
				'title': 'Error parsing recipe',
				'ingredients': [],
				'instructions': [],
				'description': 'Failed to extract recipe content'
			}
		}

# Convenience function for backward compatibility
def scrape_recipe_page_enhanced(url: str, max_retries: int = 3) -> str:
	"""Enhanced version of the original scrape_recipe_page function."""
	scraper = EnhancedRecipeScraper()
	result = scraper.scrape_recipe(url, max_retries)
	
	if result['success']:
		recipe = result['recipe']
		
		# Format the output similar to the original function
		content_parts = []
		
		if recipe['title']:
			content_parts.append(f"Title: {recipe['title']}")
		
		if recipe['description']:
			content_parts.append(f"Description: {recipe['description']}")
		
		if recipe['ingredients']:
			content_parts.append("Ingredients:\n" + "\n".join(f"- {ing}" for ing in recipe['ingredients']))
		
		if recipe['instructions']:
			content_parts.append("Instructions:\n" + "\n".join(f"{i+1}. {step}" for i, step in enumerate(recipe['instructions'])))
		
		return "\n\n".join(content_parts)
	else:
		return f"Error scraping recipe: {result['error']}"

if __name__ == "__main__":
	# Test the enhanced scraper
	import sys
	
	if len(sys.argv) < 2:
		print("Usage: python enhanced_scraping.py <recipe_url>")
		sys.exit(1)
	
	url = sys.argv[1]
	scraper = EnhancedRecipeScraper()
	result = scraper.scrape_recipe(url)
	
	if result['success']:
		print("✅ Successfully scraped recipe:")
		print(f"Method used: {result['method']}")
		print(f"Title: {result['recipe']['title']}")
		print(f"Ingredients: {len(result['recipe']['ingredients'])} items")
		print(f"Instructions: {len(result['recipe']['instructions'])} steps")
	else:
		print(f"❌ Failed to scrape recipe: {result['error']}")
