# process_recipe.py
import json
from openai import OpenAI
import os

# Make sure you have set your OpenAI API key:
# export OPENAI_API_KEY="sk-XXXX..."

# Initialize the client
client = OpenAI()  # This automatically uses your OPENAI_API_KEY environment variable

def parse_and_structure_recipe(raw_text: str) -> dict:
    """
    Sends the raw recipe text (or JSON-LD) to OpenAI and requests a structured JSON response.
    """

    prompt = f"""
    You are a helpful assistant. I have some raw text extracted from a recipe webpage below.
    Please read the content and extract the following in JSON format:

    1) "introduction": A very short introduction (1-2 sentences).
    2) "ingredients": An array of objects with {{"quantity": "", "item": ""}}.
    3) "instructions": An array of steps. Do not prefix with "Step X:" - just include the instruction text.

    Return valid JSON with this structure:
    {{
      "introduction": "string",
      "ingredients": [
        {{"quantity": "1 tsp", "item": "salt"}}
      ],
      "instructions": [
        "Mix salt with other ingredients",
        "Cook for 30 minutes"
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
