# process_recipe.py
import copy
import json
import logging
import os
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

logger = logging.getLogger(__name__)

api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    print("WARNING: No OpenAI API key found. Please set the OPENAI_API_KEY environment variable.")
    # Don't raise error immediately - let the app start and handle it gracefully
    client = None
else:
    client = OpenAI(api_key=api_key)


def _is_complete_structured_recipe(data: Any) -> bool:
    """Return True when the dict has the minimum fields the UI requires."""
    if not isinstance(data, dict):
        return False
    if not data.get('title'):
        return False
    ingredients = data.get('ingredients')
    instructions = data.get('instructions')
    return bool(ingredients) and bool(instructions)


def _coerce_to_structured_recipe(
    candidate: Any, fallback: Optional[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """
    Merge a (possibly partial) LLM response with a deterministic fallback so
    the user always gets a usable recipe when JSON-LD is available.
    Returns None when neither source produces a usable recipe.
    """
    if _is_complete_structured_recipe(candidate):
        return candidate

    if fallback and _is_complete_structured_recipe(fallback):
        merged = copy.deepcopy(fallback)
        if isinstance(candidate, dict):
            for key in ('title', 'introduction', 'ingredients', 'instructions'):
                value = candidate.get(key)
                if value:
                    merged[key] = value
        return merged

    return candidate if isinstance(candidate, dict) else None


def parse_and_structure_recipe(
    raw_text: str,
    fallback_structured_recipe: Optional[Dict[str, Any]] = None,
) -> dict:
    """
    Sends the raw recipe text (or JSON-LD) to OpenAI and requests a structured JSON response.

    When `fallback_structured_recipe` is provided (typically built from JSON-LD
    by the scraper), it is used as a deterministic safety net: if the LLM call
    fails entirely, or returns a payload that is missing required fields, the
    fallback is used (or merged with the partial LLM response) so callers
    receive a usable recipe instead of an opaque parsing error.
    """

    prompt = f"""
    You are a helpful assistant. I have some raw text extracted from a recipe webpage below.
    Please read the content and extract the following in JSON format:

    1) "title": The recipe title.
    2) "introduction": A very short introduction (1-2 sentences).
    3) "ingredients": An array of objects with {{"quantity": "", "item": ""}}.
    4) "instructions": An array of steps. IMPORTANT: Each instruction step must include the specific quantities from the ingredients list when that ingredient is first used.

    Return valid JSON with this structure:
    {{
      "title": "Recipe Title",
      "introduction": "string",
      "ingredients": [
        {{"quantity": "2 cups", "item": "flour"}},
        {{"quantity": "1 tsp", "item": "salt"}}
      ],
      "instructions": [
        "In a large bowl, mix 2 cups of flour with 1 tsp salt",
        "Knead the dough for 10 minutes"
      ]
    }}

    Raw recipe text:
    {raw_text}
    """

    error_payload = {
        "title": "Error parsing recipe",
        "introduction": "There was an error processing this recipe.",
        "ingredients": [],
        "instructions": []
    }

    if client is None:
        if _is_complete_structured_recipe(fallback_structured_recipe):
            logger.info("OpenAI client unavailable; using JSON-LD fallback recipe.")
            return copy.deepcopy(fallback_structured_recipe)
        return {
            "title": "Configuration Error",
            "introduction": "OpenAI API key not configured. Please set the OPENAI_API_KEY environment variable.",
            "ingredients": [],
            "instructions": []
        }

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Cost-effective model, works great for structured JSON parsing
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},  # Ensures valid JSON response
            temperature=0.1  # Lower temperature for more consistent parsing
        )

        ai_text = response.choices[0].message.content.strip()
        print("AI Response:", ai_text)

        recipe_data = json.loads(ai_text)
        print("Structured recipe data:", recipe_data)  # Debug log

        merged = _coerce_to_structured_recipe(recipe_data, fallback_structured_recipe)
        if _is_complete_structured_recipe(merged):
            return merged

        logger.warning(
            "LLM response was missing required fields; "
            "falling back to JSON-LD recipe data if available."
        )
        if _is_complete_structured_recipe(fallback_structured_recipe):
            return copy.deepcopy(fallback_structured_recipe)

        return merged if isinstance(merged, dict) else error_payload

    except Exception as e:
        logger.exception(f"Error in parse_and_structure_recipe: {e}")
        print(f"Error in parse_and_structure_recipe: {str(e)}")
        if _is_complete_structured_recipe(fallback_structured_recipe):
            logger.info("Using JSON-LD fallback recipe after LLM failure.")
            return copy.deepcopy(fallback_structured_recipe)
        return error_payload
