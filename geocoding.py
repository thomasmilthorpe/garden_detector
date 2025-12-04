"""
Geocoding module for Garden Detector application.
Handles address lookup and street enumeration using Google Maps API.
"""

import re
import time
import random
import requests
from typing import List, Dict, Optional
from config import GOOGLE_MAPS_API_KEY, GOOGLE_MAPS_BASE_URL, API_DELAY_SHORT, API_DELAY_MEDIUM


def find_nearest_house_number(lat: float, lon: float, street_name: str, suburb: str) -> Optional[int]:
    """
    Find the nearest house number to a geocentre using reverse geocoding.
    
    Args:
        lat: Latitude of geocentre
        lon: Longitude of geocentre
        street_name: Street name
        suburb: Suburb name
        
    Returns:
        House number as integer, or None if not found
    """
    # Use Google Maps reverse geocoding
    geocode_url = f"{GOOGLE_MAPS_BASE_URL}/geocode/json"
    params = {
        'latlng': f"{lat},{lon}",
        'result_type': 'street_address',
        'key': GOOGLE_MAPS_API_KEY
    }
    
    try:
        response = requests.get(geocode_url, params=params)
        data = response.json()
        
        if data['status'] == 'OK' and len(data['results']) > 0:
            for result in data['results']:
                formatted_addr = result['formatted_address']
                
                # Extract house number using regex
                match = re.match(r'^(\d+)', formatted_addr)
                if match:
                    house_number = int(match.group(1))
                    print(f"  Found nearest address to geocentre: {house_number}")
                    return house_number
        
        # If reverse geocoding didn't work, try a few nearby points
        print(f"  Could not find address at geocentre, trying nearby...")
        for offset in [0.0001, -0.0001, 0.0002, -0.0002]:
            test_lat = lat + offset
            test_lon = lon + offset
            
            params = {
                'latlng': f"{test_lat},{test_lon}",
                'result_type': 'street_address',
                'key': GOOGLE_MAPS_API_KEY
            }
            
            response = requests.get(geocode_url, params=params)
            data = response.json()
            
            if data['status'] == 'OK' and len(data['results']) > 0:
                formatted_addr = data['results'][0]['formatted_address']
                match = re.match(r'^(\d+)', formatted_addr)
                if match:
                    house_number = int(match.group(1))
                    print(f"  Found nearby address: {house_number}")
                    return house_number
            
            time.sleep(API_DELAY_SHORT)
        
        return None
        
    except Exception as e:
        print(f"  Error finding nearest house number: {e}")
        return None


def is_residential(result: Dict) -> bool:
    """
    Check if a geocoding result is a residential address.
    
    Args:
        result: Geocoding API result dictionary
        
    Returns:
        True if residential, False otherwise
    """
    # Check address components for residential indicators
    address_components = result.get('address_components', [])
    types = result.get('types', [])
    
    # Primary check: look for street_address type and absence of commercial types
    is_street_address = 'street_address' in types
    
    # Check for non-residential types that should be excluded
    non_residential_types = {
        'airport', 'amusement_park', 'aquarium', 'art_gallery', 'bakery',
        'bank', 'bar', 'beauty_salon', 'bicycle_store', 'book_store',
        'bowling_alley', 'bus_station', 'cafe', 'campground', 'car_dealer',
        'car_rental', 'car_repair', 'car_wash', 'casino', 'cemetery',
        'church', 'city_hall', 'clothing_store', 'convenience_store',
        'courthouse', 'dentist', 'department_store', 'doctor', 'drugstore',
        'electrician', 'electronics_store', 'embassy', 'fire_station',
        'florist', 'funeral_home', 'furniture_store', 'gas_station', 'gym',
        'hair_care', 'hardware_store', 'hindu_temple', 'home_goods_store',
        'hospital', 'insurance_agency', 'jewelry_store', 'laundry',
        'lawyer', 'library', 'light_rail_station', 'liquor_store',
        'local_government_office', 'locksmith', 'lodging', 'meal_delivery',
        'meal_takeaway', 'mosque', 'movie_rental', 'movie_theater',
        'moving_company', 'museum', 'night_club', 'painter', 'park',
        'parking', 'pet_store', 'pharmacy', 'physiotherapist', 'plumber',
        'police', 'post_office', 'primary_school', 'real_estate_agency',
        'restaurant', 'roofing_contractor', 'rv_park', 'school',
        'secondary_school', 'shoe_store', 'shopping_mall', 'spa', 'stadium',
        'storage', 'store', 'subway_station', 'supermarket', 'synagogue',
        'taxi_stand', 'tourist_attraction', 'train_station', 'transit_station',
        'travel_agency', 'university', 'veterinary_care', 'zoo',
        'establishment', 'point_of_interest'
    }
    
    # Check if any non-residential types are present
    has_commercial_type = any(t in non_residential_types for t in types)
    
    # If it's a street address and doesn't have commercial types, it's likely residential
    if is_street_address and not has_commercial_type:
        return True
    
    # Additional check: if it's ROOFTOP precision and has subpremise, it's likely residential
    location_type = result.get('geometry', {}).get('location_type')
    has_subpremise = any(comp.get('types', []) == ['subpremise'] for comp in address_components)
    
    if location_type == 'ROOFTOP' and not has_commercial_type:
        return True
    
    return False


def enumerate_street_addresses(street_name: str, suburb: str, center_location: Dict, 
                               num_addresses: int = 20, min_number: Optional[int] = None, 
                               max_number: Optional[int] = None) -> List[Dict]:
    """
    Enumerate addresses along a street by trying house numbers.
    
    Args:
        street_name: Street name
        suburb: Suburb name
        center_location: Dictionary with 'lat' and 'lng' or 'lon' keys
        num_addresses: Maximum number of addresses to find
        min_number: Minimum house number to search (manual mode)
        max_number: Maximum house number to search (manual mode)
        
    Returns:
        List of valid addresses
    """
    addresses = []
    
    # Get lat/lon from center_location (handle both 'lng' and 'lon' keys)
    center_lat = center_location.get('lat')
    center_lon = center_location.get('lon') or center_location.get('lng')
    
    # Determine house number range
    if min_number is not None and max_number is not None:
        # Manual mode: use provided range
        print(f"Using manual range: {min_number} to {max_number}")
        house_numbers = list(range(min_number, max_number + 1))
    else:
        # Auto mode: find nearest house number and search around it
        print(f"Using auto mode to determine address range...")
        print(f"Finding nearest address to street geocentre...")
        nearest_number = find_nearest_house_number(center_lat, center_lon, street_name, suburb)
        
        if nearest_number:
            # Search from (nearest - 200) to (nearest + 200)
            start_num = max(1, nearest_number - 200)
            end_num = nearest_number + 200
            print(f"Searching house numbers from {start_num} to {end_num}...")
            house_numbers = list(range(start_num, end_num + 1))
        else:
            # Fallback to common ranges if we couldn't find a nearest number
            print(f"Could not determine nearest address, trying common ranges...")
            house_numbers = list(range(1, 201)) + list(range(100, 301)) + list(range(200, 401))
    
    print(f"Attempting to find valid addresses...")
    found_count = 0
    consecutive_skips = 0
    current_index = 0
    
    while found_count < num_addresses and current_index < len(house_numbers):
        num = house_numbers[current_index]
        current_index += 1
        
        full_address = f"{num} {street_name}, {suburb}"
        
        # Geocode this specific address
        geocode_url = f"{GOOGLE_MAPS_BASE_URL}/geocode/json"
        params = {
            'address': full_address,
            'key': GOOGLE_MAPS_API_KEY
        }
        
        try:
            response = requests.get(geocode_url, params=params)
            data = response.json()
            
            if data['status'] == 'OK' and len(data['results']) > 0:
                result = data['results'][0]
                location_type = result['geometry']['location_type']
                
                # Only accept precise addresses
                if location_type in ['ROOFTOP']:
                    formatted_addr = result['formatted_address']
                    
                    # Check if this address actually contains our street name
                    # (to avoid getting addresses from nearby streets)
                    street_variants = [
                        street_name.lower(),
                        street_name.lower().replace(' street', ' st'),
                        street_name.lower().replace(' st', ' street'),
                        street_name.lower().replace(' avenue', ' ave'),
                        street_name.lower().replace(' ave', ' avenue'),
                        street_name.lower().replace(' road', ' rd'),
                        street_name.lower().replace(' rd', ' road'),
                        street_name.lower().replace(' drive', ' dr'),
                        street_name.lower().replace(' dr', ' drive')
                    ]
                    
                    if any(variant in formatted_addr.lower() for variant in street_variants):
                        # Check if address is residential
                        if is_residential(result):
                            # Avoid duplicates
                            if not any(addr['address'] == formatted_addr for addr in addresses):
                                addresses.append({
                                    'address': formatted_addr,
                                    'lat': result['geometry']['location']['lat'],
                                    'lng': result['geometry']['location']['lng']
                                })
                                found_count += 1
                                consecutive_skips = 0  # Reset skip counter
                                print(f"  Found: {formatted_addr}")
                        else:
                            print(f"  Skipping {full_address} - non-residential")
                            consecutive_skips += 1
                    else:
                        consecutive_skips += 1
                else:
                    print(f"  Skipping {full_address} - location too approximate ({location_type})")
                    consecutive_skips += 1
            else:
                consecutive_skips += 1
            
            # If more than 5 consecutive skips, jump to random position
            if consecutive_skips > 5 and current_index < len(house_numbers):
                remaining_numbers = len(house_numbers) - current_index
                if remaining_numbers > 10:  # Only jump if there's enough remaining
                    jump_distance = random.randint(10, min(50, remaining_numbers - 1))
                    current_index += jump_distance
                    print(f"  Too many skips, jumping ahead {jump_distance} numbers to {house_numbers[current_index] if current_index < len(house_numbers) else 'end'}...")
                    consecutive_skips = 0  # Reset skip counter after jump
            
            # Small delay to avoid rate limiting
            if current_index % 10 == 0:
                time.sleep(API_DELAY_MEDIUM)
            else:
                time.sleep(API_DELAY_SHORT)
                
        except Exception as e:
            print(f"  Error checking {full_address}: {e}")
            consecutive_skips += 1
            continue

    print(f"\nFound {len(addresses)} valid residential addresses (tried {current_index} house numbers)")
    return addresses


def geocode_street(street_name: str, suburb: str) -> Dict:
    """
    Find the geocenter of a street using Google Maps Geocoding API.
    
    Args:
        street_name: Name of the street
        suburb: Suburb or city name
        
    Returns:
        Dictionary with 'location' (lat/lng dict) and 'formatted_address', or None if error
    """
    print(f"\nSearching for street: {street_name}, {suburb}...")
    
    # Search for the street
    search_query = f"{street_name}, {suburb}"
    geocode_url = f"{GOOGLE_MAPS_BASE_URL}/geocode/json"
    
    params = {
        'address': search_query,
        'key': GOOGLE_MAPS_API_KEY
    }
    
    response = requests.get(geocode_url, params=params)
    data = response.json()
    
    if data['status'] != 'OK':
        print(f"Error geocoding street: {data['status']}")
        return None
    
    # Get the street's location
    street_location = data['results'][0]['geometry']['location']
    formatted_address = data['results'][0]['formatted_address']
    print(f"Found street: {formatted_address}")
    
    return {
        'location': street_location,
        'formatted_address': formatted_address
    }
