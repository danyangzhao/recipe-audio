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

    1) "introduction": A very short introduction (1-2 sentences).
    2) "ingredients": An array of objects with {{"quantity": "", "item": ""}}.
    3) "instructions": An array of steps. IMPORTANT: Each instruction step must include the specific quantities from the ingredients list when that ingredient is first used. For example, if an ingredient is "2 cups flour", the instruction should say "Add 2 cups of flour" not just "Add flour".

    Return valid JSON with this structure:
    {{
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

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )

    # Extract the assistant's message
    ai_text = response.choices[0].message.content.strip()
    
    # Debug logging
    print("AI Response:", ai_text)

    # Attempt to parse the AI text as JSON
    try:
        # Clean up the response by removing markdown code block markers if present
        cleaned_text = ai_text
        if cleaned_text.startswith('```'):
            cleaned_text = cleaned_text.split('\n', 1)[1]  # Remove first line
        if cleaned_text.endswith('```'):
            cleaned_text = cleaned_text.rsplit('\n', 1)[0]  # Remove last line
        
        recipe_data = json.loads(cleaned_text)
        print("Parsed Recipe Data:", json.dumps(recipe_data, indent=2))
    except json.JSONDecodeError as e:
        print(f"JSON Parse Error: {str(e)}")
        recipe_data = {"raw_text": ai_text}

    return recipe_data
