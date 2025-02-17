# tts.py
from openai import OpenAI
import os

def generate_audio_from_text(text: str) -> bytes:
    """
    Converts text to speech using OpenAI's Text-to-Speech API.
    Returns raw audio bytes in MP3 format.
    
    Requires:
    - OPENAI_API_KEY environment variable to be set
    - openai package installed (>1.0.0)
    """
    # Add debug logging
    print(f"Generating audio for text ({len(text)} chars):")
    print(f"Text preview: {text[:200]}...")  # Print first 200 chars
    
    client = OpenAI()  # Automatically uses OPENAI_API_KEY from environment

    # Generate speech using OpenAI's TTS API
    response = client.audio.speech.create(
        model="tts-1-hd",  # Using HD model for better quality
        voice="nova",      # Using nova voice for clearer speech
        input=text
    )

    # Get the audio content as bytes
    audio_content = response.content
    
    # Add debug logging
    print(f"Generated audio size: {len(audio_content)} bytes")
    
    return audio_content
