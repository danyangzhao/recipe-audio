# app.py
from flask import Flask, request, jsonify, render_template, abort
from scrape import scrape_recipe_page
from enhanced_scraping import scrape_recipe_page_enhanced
from process_recipe import parse_and_structure_recipe
from models import db, Recipe
from storage import AudioStorage

import os
import time
from dotenv import load_dotenv
from openai import OpenAI
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)

# Load environment variables from .env file (for local development)
load_dotenv()

# Get the API key from environment variables
openai_api_key = os.getenv('OPENAI_API_KEY')

if not openai_api_key:
    print("WARNING: No OpenAI API key found. Please set the OPENAI_API_KEY environment variable.")
    client = None
else:
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

# Add connection timeout for PostgreSQL to prevent hanging
if DATABASE_URL and 'postgresql' in DATABASE_URL:
    app.config['SQLALCHEMY_ENGINE_OPTIONS']['connect_args'] = {
        'connect_timeout': 10  # 10 second connection timeout
    }

db.init_app(app)

# Initialize database tables (non-blocking - we'll handle errors gracefully in routes)
with app.app_context():
    try:
        db.create_all()
        print("✅ Database tables created successfully!")
    except Exception as e:
        print(f"⚠️  Database initialization warning (will retry on first request): {e}")

# Create audio storage directory
AUDIO_FOLDER = 'static/audio'
if not os.path.exists(AUDIO_FOLDER):
    os.makedirs(AUDIO_FOLDER)

storage = AudioStorage()

@app.route('/health')
def health():
    """Health check endpoint for Railway"""
    # Simple health check - don't query database to avoid startup delays
    return jsonify({
        'status': 'healthy',
        'openai_configured': client is not None
    }), 200

@app.route('/migrate')
def migrate_database():
    """Database migration endpoint for Railway"""
    try:
        from migrate_db import main as run_migration
        run_migration()
        return jsonify({
            'status': 'success',
            'message': 'Database migration completed successfully'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Migration failed: {str(e)}'
        }), 500

@app.route('/')
def index():
    """Serve the main page with popular recipes"""
    # Check if OpenAI is configured
    config_error = None
    if client is None:
        config_error = "OpenAI API key not configured. Please set the OPENAI_API_KEY environment variable."
    
    # Try to fetch popular recipes, but don't fail the page load if database is unavailable
    popular_recipes = []
    try:
        popular_recipes = Recipe.query.order_by(Recipe.views.desc()).limit(10).all()
    except Exception as e:
        print(f"Database error: {e}")
        if not config_error:
            config_error = "Database connection issue. Please check the migration endpoint: /migrate"
    
    return render_template('index.html', popular_recipes=popular_recipes, config_error=config_error)

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
        # 0. If recipe already exists, return it instead of inserting a duplicate
        existing_recipe = Recipe.query.filter_by(url=recipe_url).first()
        if existing_recipe:
            existing_structured = {
                'id': existing_recipe.id,
                'title': existing_recipe.title,
                'introduction': existing_recipe.introduction,
                'ingredients': existing_recipe.ingredients,
                'instructions': existing_recipe.instructions,
                'audio_filename': existing_recipe.audio_filename,
                'audio_url': existing_recipe.audio_url,
            }
            return jsonify({
                'success': True,
                'recipe': existing_structured
            })

        # 1. Scrape the webpage with fallback to enhanced scraper
        raw_text = scrape_recipe_page(recipe_url)
        
        # If original scraper fails, try enhanced scraper
        if raw_text.startswith('Error scraping recipe:') or raw_text == "No recipe content found":
            print(f"Original scraper failed, trying enhanced scraper for: {recipe_url}")
            raw_text = scrape_recipe_page_enhanced(recipe_url)
        
        # Check if both scrapers failed
        if raw_text.startswith('Error scraping recipe:'):
            return jsonify({'error': raw_text}), 400
        
        # 2. Parse & structure with OpenAI
        structured_recipe = parse_and_structure_recipe(raw_text)
        
        # Validate the structured recipe has required fields
        if not structured_recipe.get('title') or not structured_recipe.get('ingredients') or not structured_recipe.get('instructions'):
            return jsonify({'error': 'Failed to parse recipe structure properly'}), 400

        # 3. Only save to database if we have a valid recipe
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

    except IntegrityError:
        # Handle race condition or duplicate insert attempts
        db.session.rollback()
        existing_recipe = Recipe.query.filter_by(url=recipe_url).first()
        if existing_recipe:
            existing_structured = {
                'id': existing_recipe.id,
                'title': existing_recipe.title,
                'introduction': existing_recipe.introduction,
                'ingredients': existing_recipe.ingredients,
                'instructions': existing_recipe.instructions,
                'audio_filename': existing_recipe.audio_filename,
                'audio_url': existing_recipe.audio_url,
            }
            return jsonify({
                'success': True,
                'recipe': existing_structured
            })
        return jsonify({'error': 'Duplicate URL and unable to fetch existing record'}), 409

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

        # Check if OpenAI client is available
        if client is None:
            return jsonify({'error': 'OpenAI API key not configured. Please set the OPENAI_API_KEY environment variable.'}), 500

        # Generate audio using OpenAI
        response = client.audio.speech.create(
            model="tts-1-hd",  # Using HD model for better quality
            voice="nova",      # Using nova voice for clearer speech
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

if __name__ == '__main__':
    # For local dev only
    # In production, use a proper WSGI server (e.g., gunicorn)
    app.run(port=5000, debug=True)
