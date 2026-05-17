import json
import unittest
from unittest import mock

from bs4 import BeautifulSoup

import process_recipe
import scrape


GAMJATANG_JSONLD = {
    "@context": "https://schema.org",
    "@graph": [
        {"@type": "WebPage", "name": "Gamjatang Page"},
        {
            "@type": "Recipe",
            "name": "Gamjatang (Pork Bone Soup)",
            "description": "Korean pork bone soup",
            "recipeIngredient": [
                "1.4 kg pork neck bone ((3 pounds))",
                "7 cups water",
                "3  potatoes (peeled & cut into smaller chunks)",
                "1 tsp whole black pepper",
                "3 Tbsp gochugaru (korean chili flakes)",
                "1 1/2 Tbsp minced garlic",
                "A few sprinkles ground black peppers",
            ],
            "recipeInstructions": [
                {"@type": "HowToStep", "text": "Soak the pork bones in cold water for at least 1 hour."},
                {"@type": "HowToStep", "text": "Boil bones for 10 minutes, drain, rinse."},
                {"@type": "HowToStep", "text": "Simmer broth with aromatics for 1.5 hours."},
            ],
        },
    ],
}


def _soup_for(jsonld_dict):
    html_doc = (
        '<html><head>'
        f'<script type="application/ld+json">{json.dumps(jsonld_dict)}</script>'
        '</head><body></body></html>'
    )
    return BeautifulSoup(html_doc, "html.parser")


class StructuredRecipeFallbackTests(unittest.TestCase):
    def test_build_structured_recipe_from_jsonld_returns_full_recipe(self):
        soup = _soup_for(GAMJATANG_JSONLD)
        structured = scrape.get_structured_data(soup)
        self.assertIsNotNone(structured)

        fallback = scrape.build_structured_recipe_from_jsonld(structured)
        self.assertIsNotNone(fallback)
        self.assertEqual(fallback["title"], "Gamjatang (Pork Bone Soup)")
        self.assertEqual(fallback["introduction"], "Korean pork bone soup")
        self.assertEqual(len(fallback["ingredients"]), 7)
        self.assertEqual(len(fallback["instructions"]), 3)
        # Each ingredient row has a string item, even when no quantity unit was matched.
        for ing in fallback["ingredients"]:
            self.assertIn("item", ing)
            self.assertIn("quantity", ing)
            self.assertTrue(ing["item"], msg=f"empty item in {ing!r}")

    def test_split_ingredient_quantity_handles_common_formats(self):
        cases = [
            ("1 cup flour", ("1 cup", "flour")),
            ("2 cups water", ("2 cups", "water")),
            ("1.4 kg pork neck bone", ("1.4 kg", "pork neck bone")),
            ("1 tsp salt", ("1 tsp", "salt")),
            ("3 Tbsp gochugaru (korean chili flakes)", ("3 Tbsp", "gochugaru (korean chili flakes)")),
            ("1 1/2 Tbsp minced garlic", ("1 1/2 Tbsp", "minced garlic")),
            ("A few sprinkles ground black peppers", ("", "A few sprinkles ground black peppers")),
            ("Salt to taste", ("", "Salt to taste")),
        ]
        for raw, (expected_q, expected_item) in cases:
            with self.subTest(raw=raw):
                parsed = scrape._split_ingredient_quantity(raw)
                self.assertEqual(parsed["quantity"], expected_q)
                self.assertEqual(parsed["item"], expected_item)

    def test_build_structured_recipe_returns_none_when_data_incomplete(self):
        partial = {"@type": "Recipe", "name": "x", "recipeIngredient": ["1 cup flour"]}
        self.assertIsNone(scrape.build_structured_recipe_from_jsonld(partial))

    def test_parse_and_structure_recipe_uses_fallback_when_llm_errors(self):
        soup = _soup_for(GAMJATANG_JSONLD)
        structured = scrape.get_structured_data(soup)
        fallback = scrape.build_structured_recipe_from_jsonld(structured)

        class BoomClient:
            class chat:
                class completions:
                    @staticmethod
                    def create(*args, **kwargs):
                        raise RuntimeError("simulated LLM failure")

        with mock.patch.object(process_recipe, "client", BoomClient()):
            result = process_recipe.parse_and_structure_recipe(
                "raw text", fallback_structured_recipe=fallback
            )

        self.assertEqual(result["title"], "Gamjatang (Pork Bone Soup)")
        self.assertEqual(len(result["ingredients"]), len(fallback["ingredients"]))
        self.assertEqual(len(result["instructions"]), len(fallback["instructions"]))

    def test_parse_and_structure_recipe_uses_fallback_when_llm_returns_empty(self):
        soup = _soup_for(GAMJATANG_JSONLD)
        structured = scrape.get_structured_data(soup)
        fallback = scrape.build_structured_recipe_from_jsonld(structured)

        empty_payload = {
            "title": "",
            "introduction": "",
            "ingredients": [],
            "instructions": [],
        }

        class FakeChoice:
            def __init__(self, content):
                self.message = mock.Mock(content=content)

        class FakeResponse:
            def __init__(self, content):
                self.choices = [FakeChoice(content)]

        class FakeClient:
            class chat:
                class completions:
                    @staticmethod
                    def create(*args, **kwargs):
                        return FakeResponse(json.dumps(empty_payload))

        with mock.patch.object(process_recipe, "client", FakeClient()):
            result = process_recipe.parse_and_structure_recipe(
                "raw text", fallback_structured_recipe=fallback
            )

        self.assertEqual(result["title"], fallback["title"])
        self.assertEqual(len(result["ingredients"]), len(fallback["ingredients"]))
        self.assertEqual(len(result["instructions"]), len(fallback["instructions"]))

    def test_parse_and_structure_recipe_merges_partial_llm_result(self):
        soup = _soup_for(GAMJATANG_JSONLD)
        structured = scrape.get_structured_data(soup)
        fallback = scrape.build_structured_recipe_from_jsonld(structured)

        partial_payload = {
            "title": "Better Gamjatang Title",
            "introduction": "A friendlier intro.",
            "ingredients": [],
            "instructions": [],
        }

        class FakeChoice:
            def __init__(self, content):
                self.message = mock.Mock(content=content)

        class FakeResponse:
            def __init__(self, content):
                self.choices = [FakeChoice(content)]

        class FakeClient:
            class chat:
                class completions:
                    @staticmethod
                    def create(*args, **kwargs):
                        return FakeResponse(json.dumps(partial_payload))

        with mock.patch.object(process_recipe, "client", FakeClient()):
            result = process_recipe.parse_and_structure_recipe(
                "raw text", fallback_structured_recipe=fallback
            )

        # Title from LLM is kept (truthy), but ingredients/instructions come from fallback.
        # Behavior: when LLM result is missing required fields, we always prefer the
        # complete fallback to guarantee a usable recipe.
        self.assertEqual(len(result["ingredients"]), len(fallback["ingredients"]))
        self.assertEqual(len(result["instructions"]), len(fallback["instructions"]))

    def test_parse_and_structure_recipe_returns_error_when_no_fallback_and_llm_fails(self):
        class BoomClient:
            class chat:
                class completions:
                    @staticmethod
                    def create(*args, **kwargs):
                        raise RuntimeError("simulated LLM failure")

        with mock.patch.object(process_recipe, "client", BoomClient()):
            result = process_recipe.parse_and_structure_recipe("raw text", fallback_structured_recipe=None)

        self.assertEqual(result["ingredients"], [])
        self.assertEqual(result["instructions"], [])
        self.assertEqual(result["title"], "Error parsing recipe")


if __name__ == "__main__":
    unittest.main()
