"""
Image processing module for Garden Detector application.
Handles satellite image retrieval and saving with property boundaries.
"""

import os
import re
import requests
from typing import Tuple, Optional
from config import GOOGLE_MAPS_API_KEY, GOOGLE_MAPS_BASE_URL, DEFAULT_ZOOM_LEVEL, DEFAULT_IMAGE_SIZE
from cadastre import draw_property_boundary_and_marker


def get_image_path(street_folder: str, address: str) -> str:
    """
    Get the expected image file path for an address.
    
    Args:
        street_folder: Folder path for the street
        address: Full address
        
    Returns:
        Full path to image file
    """
    # Extract house number for filename
    match = re.match(r'^(\d+)', address)
    if match:
        house_number = match.group(1)
        filename = f"{house_number}.jpg"
    else:
        # Fallback: use sanitized address
        filename = address.replace(' ', '_').replace(',', '').replace('/', '_')[:50] + '.jpg'
    
    return os.path.join(street_folder, filename)


def image_exists(street_folder: str, address: str) -> bool:
    """
    Check if image file already exists for an address.
    
    Args:
        street_folder: Folder path for the street
        address: Full address
        
    Returns:
        True if image exists, False otherwise
    """
    image_path = get_image_path(street_folder, address)
    return os.path.exists(image_path)


def get_satellite_image(lat: float, lng: float, zoom: int = DEFAULT_ZOOM_LEVEL, 
                       size: int = DEFAULT_IMAGE_SIZE) -> bytes:
    """
    Retrieve satellite imagery for a location using Google Maps Static API.
    
    Args:
        lat: Latitude
        lng: Longitude
        zoom: Zoom level (20 is very close, good for seeing gardens)
        size: Image size in pixels
        
    Returns:
        Image data as bytes, or None if error
    """
    static_map_url = f"{GOOGLE_MAPS_BASE_URL}/staticmap"
    
    params = {
        'center': f"{lat},{lng}",
        'zoom': zoom,
        'size': f'{size}x{size}',
        'maptype': 'satellite',
        'key': GOOGLE_MAPS_API_KEY
    }
    
    response = requests.get(static_map_url, params=params)
    
    if response.status_code == 200:
        return response.content
    else:
        print(f"Error fetching satellite image: {response.status_code}")
        return None


def save_satellite_image(image_data: bytes, street_folder: str, address: str, 
                        lat: float, lng: float, image_center_lat: float, 
                        image_center_lng: float) -> Tuple[str, bytes]:
    """
    Save satellite image with property marker to street folder.
    
    Args:
        image_data: Image data as bytes
        street_folder: Folder path to save image
        address: Full address (used for filename)
        lat: Latitude of property (geocoded address point)
        lng: Longitude of property (geocoded address point)
        image_center_lat: Latitude of the image center (property centroid)
        image_center_lng: Longitude of the image center (property centroid)
        
    Returns:
        Tuple of (filepath, annotated_image_data)
    """
    # Create folder if it doesn't exist
    os.makedirs(street_folder, exist_ok=True)
    
    # Create safe filename from address (extract house number)
    match = re.match(r'^(\d+)', address)
    if match:
        house_number = match.group(1)
        filename = f"{house_number}.jpg"
    else:
        # Fallback: use sanitized address
        filename = address.replace(' ', '_').replace(',', '').replace('/', '_')[:50] + '.jpg'
    
    filepath = os.path.join(street_folder, filename)
    
    # Draw property boundary and marker on the image
    # Note: image is centered at image_center, boundary is fetched at geocoded (lat, lng)
    annotated_image = draw_property_boundary_and_marker(
        image_data, lat, lng, image_center_lat, image_center_lng
    )
    
    # Save annotated image
    try:
        with open(filepath, 'wb') as f:
            f.write(annotated_image)
        print(f"  Saved image to: {filepath}")
        return filepath, annotated_image
    except Exception as e:
        print(f"  Error saving image: {e}")
        return filepath, image_data
