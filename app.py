# app.py
from flask import Flask, request, jsonify, send_file, render_template, Response
from scrape import scrape_recipe_page
from process_recipe import parse_and_structure_recipe
from tts import generate_audio_from_text  # or use the google TTS function

import os
import io
import time
from dotenv import load_dotenv
from openai import OpenAI
import tempfile
import gc  # For garbage collection

app = Flask(__name__)

# Load environment variables from .env file (for local development)
load_dotenv()

# Get the API key from environment variables
openai_api_key = os.getenv('OPENAI_API_KEY')

if not openai_api_key:
    raise ValueError("No OpenAI API key found. Please set the OPENAI_API_KEY environment variable.")

# Configure your OpenAI client
client = OpenAI(api_key=openai_api_key)

@app.route('/')
def index():
    """Serve the main page with the URL input form"""
    return render_template('index.html')

@app.route('/result')
def result():
    """Serve the result page that displays the recipe and audio controls"""
    return render_template('result.html')

@app.route('/extract-recipe', methods=['POST'])
def extract_recipe():
    """
    Expects JSON body: { "recipeUrl": "https://some.recipe.url" }
    Returns JSON: { "recipe": { "introduction": "...", "ingredients": [...], "instructions": [...] } }
    """
    data = request.get_json()
    recipe_url = data.get('recipeUrl')
    if not recipe_url:
        return jsonify({"error": "No recipeUrl provided"}), 400

    # 1. Scrape the webpage
    raw_text = scrape_recipe_page(recipe_url)

    # 2. Parse & structure with OpenAI
    structured_recipe = parse_and_structure_recipe(raw_text)

    return jsonify({"recipe": structured_recipe})


@app.route('/generate-audio', methods=['POST'])
def generate_audio():
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        # Limit text length to manage memory
        max_length = 3000  # Limit text length
        if len(text) > max_length:
            text = text[:max_length] + "..."
        
        try:
            # Force garbage collection before generating audio
            gc.collect()
            
            # Generate audio with minimal settings
            response = client.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=text,
                speed=1.0  # Default speed to minimize processing
            )
            
            # Stream the response directly without storing in memory
            def generate():
                yield from response.iter_bytes(chunk_size=4096)
            
            return Response(generate(), mimetype='audio/mpeg')
            
        except Exception as e:
            print(f"Error generating audio: {str(e)}")
            return jsonify({'error': 'Failed to generate audio'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        # Force cleanup
        gc.collect()

@app.route('/results')
def results():
    # Assuming recipe_data is stored in a session or passed as a parameter
    recipe_data = {
        "title": "Recipe Title",
        "description": "Recipe description...",
        "ingredients": ["ingredient 1", "ingredient 2", ...],
        "instructions": ["step 1", "step 2", ...],
        "notes": "Optional notes..."
    }
    return render_template('results.html', recipe=recipe_data)

if __name__ == '__main__':
    # For local dev only
    # In production, use a proper WSGI server (e.g., gunicorn)
    app.run(port=5000, debug=True)
