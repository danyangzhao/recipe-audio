import os
import unittest

from scrape import scrape_recipe_page


RUN_LIVE_RECIPE_SITE_TESTS = os.getenv("RUN_LIVE_RECIPE_SITE_TESTS") == "1"

LIVE_TOP_25_RECIPE_URLS = [
    ("allrecipes.com", "https://www.allrecipes.com/recipe/10813/best-chocolate-chip-cookies/"),
    ("delish.com", "https://www.delish.com/cooking/recipe-ideas/a20089653/classic-burger-recipe/"),
    ("bonappetit.com", "https://www.bonappetit.com/recipe/bas-best-chocolate-chip-cookies"),
    ("tasteofhome.com", "https://www.tasteofhome.com/recipes/basic-homemade-bread/"),
    ("simplyrecipes.com", "https://www.simplyrecipes.com/recipes/perfect_guacamole/"),
    ("bbcgoodfood.com", "https://www.bbcgoodfood.com/recipes/easy-pancakes"),
    ("loveandlemons.com", "https://www.loveandlemons.com/chocolate-chip-cookies/"),
    ("sallysbakingaddiction.com", "https://sallysbakingaddiction.com/chewy-chocolate-chip-cookies/"),
    ("skinnytaste.com", "https://www.skinnytaste.com/chicken-parmesan/"),
    ("halfbakedharvest.com", "https://www.halfbakedharvest.com/one-pot-creamy-french-onion-pasta-bake/"),
    ("recipetineats.com", "https://www.recipetineats.com/chicken-stir-fry/"),
    ("natashaskitchen.com", "https://natashaskitchen.com/banana-bread-recipe-video/"),
    ("onceuponachef.com", "https://www.onceuponachef.com/recipes/banana-bread.html"),
    ("spendwithpennies.com", "https://www.spendwithpennies.com/easy-homemade-lasagna/"),
    ("gimmesomeoven.com", "https://www.gimmesomeoven.com/baked-chicken-breast/"),
    ("inspiredtaste.net", "https://www.inspiredtaste.net/37062/juicy-skillet-pork-chops/"),
    (
        "thepioneerwoman.com",
        "https://www.thepioneerwoman.com/food-cooking/recipes/a9893/simple-pan-fried-pork-chops/",
    ),
    (
        "seriouseats.com",
        "https://www.seriouseats.com/the-best-slow-cooked-italian-american-tomato-sauce-red-sauce-recipe",
    ),
    ("jamieoliver.com", "https://www.jamieoliver.com/recipes/chicken-recipes/perfect-roast-chicken/"),
    ("marthastewart.com", "https://www.marthastewart.com/338185/basic-pancakes"),
    ("budgetbytes.com", "https://www.budgetbytes.com/chicken-stir-fry/"),
    ("wellplated.com", "https://www.wellplated.com/baked-chicken-breast/"),
    ("thechunkychef.com", "https://www.thechunkychef.com/family-favorite-baked-mac-and-cheese/"),
    ("downshiftology.com", "https://downshiftology.com/recipes/baked-chicken-breast/"),
    ("tastesbetterfromscratch.com", "https://tastesbetterfromscratch.com/banana-bread/"),
]


def _is_scrape_failure(raw_text: str) -> bool:
    if not raw_text:
        return True
    normalized = raw_text.lower()
    return (
        "error scraping recipe:" in normalized
        or "failed to extract recipe content" in normalized
        or "no recipe content found" in normalized
    )


@unittest.skipUnless(
    RUN_LIVE_RECIPE_SITE_TESTS,
    "Set RUN_LIVE_RECIPE_SITE_TESTS=1 to run live top-25 recipe site smoke tests.",
)
class LiveRecipeSiteSmokeTests(unittest.TestCase):
    def test_live_top_25_recipe_sites_extract_ingredients_and_instructions(self):
        failures = []
        for domain, url in LIVE_TOP_25_RECIPE_URLS:
            with self.subTest(domain=domain):
                content = scrape_recipe_page(url, max_retries=1)
                if _is_scrape_failure(content):
                    failures.append(f"{domain}: scraper failed with: {content[:120]}")
                    continue
                if "Ingredients:" not in content or "Instructions:" not in content:
                    failures.append(f"{domain}: missing Ingredients/Instructions sections")

        self.assertEqual([], failures, msg="\n".join(failures))


if __name__ == "__main__":
    unittest.main()
