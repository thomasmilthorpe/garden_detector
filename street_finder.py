"""
Street finder module for Garden Detector application.
Handles finding streets in a suburb using OpenStreetMap APIs.
"""

import time
import requests
from typing import List, Dict
from config import OSM_BASE_URL, OVERPASS_BASE_URL


def get_streets_in_suburb(suburb: str, max_streets: int = 10) -> List[Dict]:
    """
    Get a list of streets in a suburb using OpenStreetMap Nominatim API.
    
    Args:
        suburb: Suburb or city name
        max_streets: Maximum number of streets to return
        
    Returns:
        List of street dictionaries with name and geocentre
    """
    print(f"\nFetching streets in {suburb} from OpenStreetMap...")
    
    # First, get the suburb boundary
    search_url = f"{OSM_BASE_URL}/search"
    params = {
        'q': suburb,
        'format': 'json',
        'limit': 1,
        'addressdetails': 1
    }
    
    headers = {
        'User-Agent': 'GardenDetectorApp/1.0'
    }
    
    try:
        response = requests.get(search_url, params=params, headers=headers)
        data = response.json()
        
        if not data:
            print(f"Could not find suburb: {suburb}")
            return []
        
        suburb_data = data[0]
        bbox = suburb_data.get('boundingbox')
        
        if not bbox:
            print(f"Could not get boundary for {suburb}")
            return []
        
        # bbox format: [min_lat, max_lat, min_lon, max_lon]
        print(f"Found suburb: {suburb_data.get('display_name')}")
        
        # Use Overpass API to get all residential streets in the suburb
        overpass_url = OVERPASS_BASE_URL
        
        # Query for residential streets within the bounding box
        overpass_query = f"""
        [out:json];
        (
          way["highway"~"^(residential|tertiary|secondary|living_street)$"]({bbox[0]},{bbox[2]},{bbox[1]},{bbox[3]});
        );
        out center;
        """
        
        time.sleep(1)  # Be nice to OSM
        response = requests.post(overpass_url, data={'data': overpass_query}, headers=headers)
        overpass_data = response.json()
        
        streets = []
        seen_names = set()
        
        for element in overpass_data.get('elements', []):
            street_name = element.get('tags', {}).get('name')
            if street_name and street_name not in seen_names:
                center = element.get('center', {})
                if center:
                    streets.append({
                        'name': street_name,
                        'lat': center.get('lat'),
                        'lon': center.get('lon')
                    })
                    seen_names.add(street_name)
                    
                    if len(streets) >= max_streets:
                        break
        
        print(f"Found {len(streets)} streets in {suburb}")
        return streets[:max_streets]
        
    except Exception as e:
        print(f"Error fetching streets from OSM: {e}")
        return []
