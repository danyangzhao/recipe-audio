# process_recipe.py
import json
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Get API key
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    raise ValueError("No OpenAI API key found. Please set the OPENAI_API_KEY environment variable.")

# Initialize the client with the API key
client = OpenAI(api_key=api_key)

def parse_and_structure_recipe(raw_text: str) -> dict:
    """
    Sends the raw recipe text (or JSON-LD) to OpenAI and requests a structured JSON response.
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

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )

        # Extract the assistant's message and clean it
        ai_text = response.choices[0].message.content.strip()
        # Remove markdown code block syntax if present
        ai_text = ai_text.replace('```json', '').replace('```', '').strip()
        print("AI Response:", ai_text)

        # Parse JSON response
        recipe_data = json.loads(ai_text)
        print("Structured recipe data:", recipe_data)  # Debug log
        return recipe_data
    except Exception as e:
        print(f"Error in parse_and_structure_recipe: {str(e)}")
        return {
            "title": "Error parsing recipe",
            "introduction": "There was an error processing this recipe.",
            "ingredients": [],
            "instructions": []
        }
