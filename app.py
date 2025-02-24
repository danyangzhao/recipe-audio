# app.py
from flask import Flask, request, jsonify, send_file, render_template, Response
from scrape import scrape_recipe_page
from process_recipe import parse_and_structure_recipe
from tts import generate_audio_from_text  # or use the google TTS function
from models import db, Recipe
from flask import url_for
from storage import AudioStorage

import os
import io
import time
from dotenv import load_dotenv
from openai import OpenAI
import tempfile
import gc  # For garbage collection
from urllib.parse import urlparse

app = Flask(__name__)

# Load environment variables from .env file (for local development)
load_dotenv()

# Get the API key from environment variables
openai_api_key = os.getenv('OPENAI_API_KEY')

if not openai_api_key:
    raise ValueError("No OpenAI API key found. Please set the OPENAI_API_KEY environment variable.")

# Configure your OpenAI client
client = OpenAI(api_key=openai_api_key)

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL:
    # Handle Heroku's "postgres://" vs "postgresql://" difference
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_size': 1,
        'max_overflow': 2,
        'pool_timeout': 30,
        'pool_recycle': 1800,
    }
else:
    # Fallback for local development
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///recipes.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Create audio storage directory
AUDIO_FOLDER = 'static/audio'
if not os.path.exists(AUDIO_FOLDER):
    os.makedirs(AUDIO_FOLDER)

storage = AudioStorage()

@app.route('/')
def index():
    """Serve the main page with popular recipes"""
    popular_recipes = Recipe.query.order_by(Recipe.views.desc()).limit(5).all()
    return render_template('index.html', popular_recipes=popular_recipes)

@app.route('/recipe/<int:recipe_id>')
def view_recipe(recipe_id):
    recipe = db.session.get(Recipe, recipe_id)
    if not recipe:
        abort(404)
    recipe.views += 1
    db.session.commit()
    
    # Convert recipe to dictionary before passing to template
    recipe_dict = {
        "title": recipe.title,
        "introduction": recipe.introduction,
        "ingredients": recipe.ingredients,
        "instructions": recipe.instructions,
        "id": recipe.id,
        "audio_filename": recipe.audio_filename,
        "audio_url": recipe.audio_url,
        "views": recipe.views
    }
    
    return render_template('stored_recipe.html', recipe=recipe_dict)

@app.route('/result')
def result():
    """Serve the result page that displays the recipe and audio controls"""
    return render_template('result.html')

@app.route('/extract-recipe', methods=['POST'])
def extract_recipe():
    data = request.get_json()
    recipe_url = data.get('recipeUrl')

    if not recipe_url:
        return jsonify({'error': 'No URL provided'}), 400

    try:
        # 1. Scrape the webpage
        raw_text = scrape_recipe_page(recipe_url)
        
        # 2. Parse & structure with OpenAI
        structured_recipe = parse_and_structure_recipe(raw_text)
        
        # 3. Save to database
        new_recipe = Recipe(
            url=recipe_url,
            title=structured_recipe.get('title'),
            introduction=structured_recipe.get('introduction'),
            ingredients=structured_recipe.get('ingredients'),
            instructions=structured_recipe.get('instructions')
        )
        db.session.add(new_recipe)
        db.session.commit()
        
        # Include the ID in the response
        structured_recipe['id'] = new_recipe.id
        
        return jsonify({
            'success': True,
            'recipe': structured_recipe
        })

    except Exception as e:
        print(f"Error extracting recipe: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/generate-audio', methods=['POST'])
def generate_audio():
    try:
        data = request.get_json()
        text = data.get('text', '')
        recipe_id = data.get('recipeId')

        if not text:
            return jsonify({'error': 'No text provided'}), 400

        # Generate unique filename
        timestamp = int(time.time())
        filename = f"recipe_{recipe_id}_{timestamp}.mp3"

        # Generate audio using OpenAI
        response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text
        )

        # Get audio content
        audio_content = response.content

        # Upload to S3
        audio_url = storage.save_audio(audio_content, filename)

        if not audio_url:
            return jsonify({'error': 'Failed to save audio'}), 500

        # Update database
        if recipe_id:
            recipe = db.session.get(Recipe, recipe_id)
            if recipe:
                recipe.audio_filename = filename
                recipe.audio_url = audio_url
                db.session.commit()

        return jsonify({
            'success': True,
            'audio_url': audio_url
        })

    except Exception as e:
        print(f"Error in generate_audio: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/results')
def results():
    # Delete this entire route as we're not using it anymore
    pass

if __name__ == '__main__':
    # For local dev only
    # In production, use a proper WSGI server (e.g., gunicorn)
    app.run(port=5000, debug=True)
