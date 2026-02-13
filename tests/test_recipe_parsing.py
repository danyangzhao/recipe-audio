import json
import unittest

from bs4 import BeautifulSoup

from scrape import extract_recipe_content, get_structured_data


TOP_25_POPULAR_RECIPE_SITES = [
    ("allrecipes.com", "https://www.allrecipes.com/recipe/10813/best-chocolate-chip-cookies/"),
    ("foodnetwork.com", "https://www.foodnetwork.com/recipes/"),
    ("delish.com", "https://www.delish.com/cooking/recipe-ideas/"),
    ("epicurious.com", "https://www.epicurious.com/recipes-menus"),
    ("bonappetit.com", "https://www.bonappetit.com/recipes"),
    ("tasteofhome.com", "https://www.tasteofhome.com/recipes/"),
    ("simplyrecipes.com", "https://www.simplyrecipes.com/"),
    ("eatingwell.com", "https://www.eatingwell.com/recipes/"),
    ("bbcgoodfood.com", "https://www.bbcgoodfood.com/recipes"),
    ("thespruceeats.com", "https://www.thespruceeats.com/recipes-4162053"),
    ("loveandlemons.com", "https://www.loveandlemons.com/recipes/"),
    ("cookieandkate.com", "https://cookieandkate.com/category/food-recipes/"),
    ("sallysbakingaddiction.com", "https://sallysbakingaddiction.com/recipes/"),
    ("minimalistbaker.com", "https://minimalistbaker.com/recipe-index/"),
    ("skinnytaste.com", "https://www.skinnytaste.com/recipes/"),
    ("halfbakedharvest.com", "https://www.halfbakedharvest.com/category/recipes/"),
    ("recipetineats.com", "https://www.recipetineats.com/"),
    ("natashaskitchen.com", "https://natashaskitchen.com/recipes/"),
    ("onceuponachef.com", "https://www.onceuponachef.com/recipes"),
    ("spendwithpennies.com", "https://www.spendwithpennies.com/recipes/"),
    ("gimmesomeoven.com", "https://www.gimmesomeoven.com/recipes/"),
    ("inspiredtaste.net", "https://www.inspiredtaste.net/recipes/"),
    ("thepioneerwoman.com", "https://www.thepioneerwoman.com/food-cooking/recipes/"),
    ("seriouseats.com", "https://www.seriouseats.com/recipes"),
    ("jamieoliver.com", "https://www.jamieoliver.com/recipes/"),
]


def _build_recipe_payload(domain: str, index: int):
    """
    Build representative JSON-LD payloads for major recipe-site structures.
    We vary wrappers and instruction formats to emulate real schema diversity.
    """
    ingredient_variants = [
        ["1 cup flour", "1 egg", "1 tbsp olive oil"],
        [{"text": "1 cup flour"}, {"name": "1 egg"}, {"item": "1 tbsp olive oil"}],
    ]

    instruction_variants = [
        [
            {"@type": "HowToStep", "text": "Whisk the egg and flour."},
            {"@type": "HowToStep", "text": "Cook until golden brown."},
        ],
        ["Whisk the egg and flour.", "Cook until golden brown."],
        {
            "@type": "HowToSection",
            "name": "Main Steps",
            "itemListElement": [
                {"@type": "HowToStep", "text": "Whisk the egg and flour."},
                {"@type": "HowToStep", "text": "Cook until golden brown."},
            ],
        },
    ]

    type_variants = [
        "Recipe",
        ["Recipe", "Thing"],
        "https://schema.org/Recipe",
    ]

    recipe = {
        "@context": "https://schema.org",
        "@type": type_variants[index % len(type_variants)],
        "name": f"Fixture recipe for {domain}",
        "description": f"Schema fixture used for {domain} parsing regression tests.",
        "recipeIngredient": ingredient_variants[index % len(ingredient_variants)],
        "recipeInstructions": instruction_variants[index % len(instruction_variants)],
    }

    wrapper_variant = index % 3
    if wrapper_variant == 0:
        return recipe
    if wrapper_variant == 1:
        return [
            {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": []},
            recipe,
        ]
    return {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "WebPage", "name": f"{domain} Recipe Page"},
            recipe,
        ],
    }


class RecipeParsingTests(unittest.TestCase):
    def test_top_25_popular_recipe_site_payloads(self):
        for index, (domain, url) in enumerate(TOP_25_POPULAR_RECIPE_SITES):
            payload = _build_recipe_payload(domain, index)
            html_doc = (
                '<html><head>'
                f'<script type="application/ld+json">{json.dumps(payload)}</script>'
                '</head><body></body></html>'
            )
            soup = BeautifulSoup(html_doc, "html.parser")

            with self.subTest(domain=domain):
                structured = get_structured_data(soup)
                self.assertIsNotNone(structured, msg=f"Failed to find recipe JSON-LD for {domain}")
                self.assertIn("name", structured, msg=f"Missing recipe name for {domain}")

                content = extract_recipe_content(soup, url)
                self.assertIn("Ingredients:", content, msg=f"Missing ingredients for {domain}")
                self.assertIn("Instructions:", content, msg=f"Missing instructions for {domain}")

    def test_inspiredtaste_style_invalid_control_chars_in_json_ld(self):
        # This payload intentionally contains literal CR/LF inside description text.
        malformed_json_ld = (
            '{"@context":"https://schema.org","@type":"Recipe",'
            '"name":"The Best Juicy Skillet Pork Chops",'
            '"description":"Author bio first line\r\nSecond line of bio",'
            '"recipeIngredient":["2 pork chops","1 tsp salt"],'
            '"recipeInstructions":['
            '{"@type":"HowToStep","text":"Season pork chops."},'
            '{"@type":"HowToStep","text":"Sear in a skillet."}'
            "]}")

        soup = BeautifulSoup(
            '<script type="application/ld+json">'
            f"{malformed_json_ld}"
            "</script>",
            "html.parser",
        )

        structured = get_structured_data(soup)
        self.assertIsNotNone(structured)
        self.assertEqual(structured.get("name"), "The Best Juicy Skillet Pork Chops")

        content = extract_recipe_content(
            soup,
            "https://www.inspiredtaste.net/37062/juicy-skillet-pork-chops/",
        )
        self.assertIn("Ingredients:", content)
        self.assertIn("Instructions:", content)
        self.assertIn("Sear in a skillet", content)


if __name__ == "__main__":
    unittest.main()
