# app.py
from flask import Flask, request, jsonify, send_file, render_template
from scrape import scrape_recipe_page
from process_recipe import parse_and_structure_recipe
from tts import generate_audio_from_text  # or use the google TTS function

import os
import io
import time
from dotenv import load_dotenv
from openai import OpenAI

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
        
        # Set a reasonable timeout for the OpenAI API call
        client.timeout = 60
        
        # Generate in smaller chunks if possible
        def generate():
            # Send initial response to keep connection alive
            yield "Processing started...\n"
            
            try:
                response = client.audio.speech.create(
                    model="tts-1",
                    voice="alloy",
                    input=data.get('text', '')
                )
                
                # Stream the response in chunks
                for chunk in response.iter_bytes(chunk_size=8192):
                    yield chunk
                    
            except Exception as e:
                print(f"Error generating audio: {str(e)}")
                yield str(e)
        
        return Response(generate(), mimetype='audio/mpeg')
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
