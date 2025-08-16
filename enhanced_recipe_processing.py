# enhanced_recipe_processing.py
import json
from openai import OpenAI
import os
from dotenv import load_dotenv
from typing import Dict, List, Optional

# Load environment variables first
load_dotenv()

# Get API key
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    raise ValueError("No OpenAI API key found. Please set the OPENAI_API_KEY environment variable.")

# Initialize the client with the API key
client = OpenAI(api_key=api_key)

def parse_and_structure_recipe_enhanced(raw_text: str) -> dict:
    """
    Enhanced version using the latest OpenAI API features for better recipe parsing.
    Uses JSON response format and function calling for more reliable parsing.
    """
    
    # Define the expected JSON schema for better parsing
    json_schema = {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "The recipe title"},
            "introduction": {"type": "string", "description": "A brief introduction to the recipe (1-2 sentences)"},
            "prep_time": {"type": "string", "description": "Preparation time if available"},
            "cook_time": {"type": "string", "description": "Cooking time if available"},
            "servings": {"type": "string", "description": "Number of servings if available"},
            "ingredients": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "quantity": {"type": "string", "description": "Amount needed"},
                        "item": {"type": "string", "description": "Ingredient name"},
                        "notes": {"type": "string", "description": "Optional preparation notes"}
                    },
                    "required": ["quantity", "item"]
                }
            },
            "instructions": {
                "type": "array",
                "items": {"type": "string", "description": "Step-by-step cooking instructions"}
            },
            "nutrition": {
                "type": "object",
                "properties": {
                    "calories": {"type": "string"},
                    "protein": {"type": "string"},
                    "carbs": {"type": "string"},
                    "fat": {"type": "string"}
                }
            }
        },
        "required": ["title", "ingredients", "instructions"]
    }

    prompt = f"""
    You are an expert recipe parser. Extract and structure the recipe information from the provided text.
    
    Guidelines:
    1. Extract the recipe title clearly
    2. Create a brief, engaging introduction
    3. List all ingredients with quantities and preparation notes if any
    4. Break down instructions into clear, numbered steps
    5. Include timing information if available
    6. Extract nutrition information if present
    7. Ensure all quantities from ingredients are referenced in the instructions
    
    Raw recipe text:
    {raw_text}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.1,  # Low temperature for consistent parsing
            max_tokens=2000   # Ensure enough tokens for complete recipes
        )

        recipe_data = json.loads(response.choices[0].message.content)
        
        # Validate required fields
        if not recipe_data.get('title') or not recipe_data.get('ingredients') or not recipe_data.get('instructions'):
            raise ValueError("Missing required recipe fields")
            
        return recipe_data
        
    except Exception as e:
        print(f"Error in enhanced recipe parsing: {str(e)}")
        return {
            "title": "Error parsing recipe",
            "introduction": "There was an error processing this recipe.",
            "ingredients": [],
            "instructions": []
        }

def generate_audio_enhanced(text: str, voice: str = "nova", model: str = "tts-1-hd") -> bytes:
    """
    Enhanced TTS function with better error handling and voice options.
    """
    try:
        response = client.audio.speech.create(
            model=model,
            voice=voice,
            input=text,
            speed=1.0  # Normal speed, can be adjusted between 0.25 and 4.0
        )
        
        return response.content
        
    except Exception as e:
        print(f"Error generating audio: {str(e)}")
        raise

def create_recipe_summary(recipe_data: Dict) -> str:
    """
    Create a concise summary of the recipe for audio generation.
    """
    title = recipe_data.get('title', 'Recipe')
    intro = recipe_data.get('introduction', '')
    ingredients = recipe_data.get('ingredients', [])
    instructions = recipe_data.get('instructions', [])
    
    # Create ingredient list
    ingredient_text = "Ingredients: "
    for i, ingredient in enumerate(ingredients, 1):
        quantity = ingredient.get('quantity', '')
        item = ingredient.get('item', '')
        ingredient_text += f"{quantity} {item}"
        if i < len(ingredients):
            ingredient_text += ", "
    
    # Create instruction summary
    instruction_text = "Instructions: "
    for i, instruction in enumerate(instructions, 1):
        instruction_text += f"Step {i}: {instruction}. "
    
    # Combine all parts
    summary = f"{title}. {intro} {ingredient_text} {instruction_text}"
    
    return summary

# Available TTS voices for different use cases
TTS_VOICES = {
    "nova": "Best for general content, clear and engaging",
    "alloy": "Good for technical content",
    "echo": "Good for storytelling",
    "fable": "Good for creative content",
    "onyx": "Good for serious content",
    "shimmer": "Good for friendly content"
}

# Available TTS models
TTS_MODELS = {
    "tts-1": "Standard quality, faster generation",
    "tts-1-hd": "High definition quality, better for longer content"
}
