"""
Configuration module for Garden Detector application.
Contains API keys, URLs, and application constants.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Validate API keys
def validate_api_keys():
    """Validate that required API keys are set."""
    if not GOOGLE_MAPS_API_KEY or GOOGLE_MAPS_API_KEY == 'your_google_maps_api_key_here':
        print("Error: Please set your Google Maps API key in the .env file")
        sys.exit(1)

    if not OPENAI_API_KEY or OPENAI_API_KEY == 'your_openai_api_key_here':
        print("Error: Please set your OpenAI API key in the .env file")
        sys.exit(1)

# API Base URLs
GOOGLE_MAPS_BASE_URL = "https://maps.googleapis.com/maps/api"
OSM_BASE_URL = "https://nominatim.openstreetmap.org"
CADASTRE_BASE_URL = "https://maps.six.nsw.gov.au/arcgis/rest/services/public/NSW_Cadastre/MapServer"
OVERPASS_BASE_URL = "https://overpass-api.de/api/interpreter"

# Application Constants
DEFAULT_ZOOM_LEVEL = 20  # Google Maps zoom level for satellite images
DEFAULT_IMAGE_SIZE = 640  # Satellite image size in pixels
DEFAULT_MAX_ADDRESSES = 20  # Default number of addresses to analyze
DEFAULT_MAX_STREETS = 5  # Default number of streets to analyze

# OpenAI Model Configuration
OPENAI_MODEL = "gpt-4o-mini"

# Rate Limiting (in seconds)
API_DELAY_SHORT = 0.1  # Short delay between API calls
API_DELAY_MEDIUM = 0.5  # Medium delay after batch operations
API_DELAY_LONG = 1.0  # Long delay to avoid throttling
