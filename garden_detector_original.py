#!/usr/bin/env python3
"""
Garden Detection Application
Analyzes Google Maps satellite imagery to detect vegetable gardens in suburban addresses.
"""

import os
import sys
import csv
import time
import re
import requests
from io import BytesIO
from typing import List, Dict, Tuple, Optional
from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image, ImageDraw

# Load environment variables
load_dotenv()

# API Configuration
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Validate API keys
if not GOOGLE_MAPS_API_KEY or GOOGLE_MAPS_API_KEY == 'your_google_maps_api_key_here':
    print("Error: Please set your Google Maps API key in the .env file")
    sys.exit(1)

if not OPENAI_API_KEY or OPENAI_API_KEY == 'your_openai_api_key_here':
    print("Error: Please set your OpenAI API key in the .env file")
    sys.exit(1)

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)


class GardenDetector:
    """Main class for detecting gardens in suburban addresses."""
    
    def __init__(self):
        self.google_maps_base_url = "https://maps.googleapis.com/maps/api"
        self.osm_base_url = "https://nominatim.openstreetmap.org"
        self.cadastre_base_url = "https://maps.six.nsw.gov.au/arcgis/rest/services/public/NSW_Cadastre/MapServer"
        self.results = []
    
    def get_street_folder(self, street_name: str, suburb: str) -> str:
        """Get the folder path for a street's analysis data."""
        safe_street = street_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
        safe_suburb = suburb.replace(' ', '_').replace('/', '_').replace('\\', '_')
        folder_name = f"{safe_street}_{safe_suburb}"
        return os.path.join(os.getcwd(), 'garden_analysis_streets', folder_name)
    
    def load_existing_addresses(self, street_name: str, suburb: str) -> Optional[List[Dict]]:
        """Load previously analyzed addresses from CSV if available."""
        street_folder = self.get_street_folder(street_name, suburb)
        csv_path = os.path.join(street_folder, f"garden_analysis_{street_name.replace(' ', '_')}_{suburb.replace(' ', '_')}.csv")
        
        if not os.path.exists(csv_path):
            return None
        
        print(f"Found existing analysis at {csv_path}")
        print("Loading previously found addresses...")
        
        addresses = []
        try:
            with open(csv_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    # Extract address, we'll need to geocode it again to get lat/lng
                    addresses.append(row['address'])
            
            # Now geocode each address to get coordinates
            geocoded_addresses = []
            for addr in addresses:
                geocode_url = f"{self.google_maps_base_url}/geocode/json"
                params = {
                    'address': addr,
                    'key': GOOGLE_MAPS_API_KEY
                }
                
                try:
                    response = requests.get(geocode_url, params=params)
                    data = response.json()
                    
                    if data['status'] == 'OK' and len(data['results']) > 0:
                        result = data['results'][0]
                        geocoded_addresses.append({
                            'address': addr,
                            'lat': result['geometry']['location']['lat'],
                            'lng': result['geometry']['location']['lng']
                        })
                    time.sleep(0.1)
                except:
                    continue
            
            print(f"Loaded {len(geocoded_addresses)} addresses from previous analysis")
            return geocoded_addresses if geocoded_addresses else None
            
        except Exception as e:
            print(f"Error loading existing addresses: {e}")
            return None
    
    def get_nsw_property_boundary(self, lat: float, lng: float) -> Optional[List[List[Tuple[float, float]]]]:
        """
        Get property boundary from NSW Cadastre MapServer.
        
        Args:
            lat: Latitude (WGS84)
            lng: Longitude (WGS84)
            
        Returns:
            List of polygon rings (outer boundary and any holes), or None if not found
        """
        try:
            # Create bounding box around the point (roughly 500m radius)
            offset = 0.005  # approximately 500m in degrees
            bbox = f"{lng - offset},{lat - offset},{lng + offset},{lat + offset}"
            
            url = f"{self.cadastre_base_url}/identify"
            
            params = {
                'geometry': f"{lng},{lat}",
                'geometryType': 'esriGeometryPoint',
                'sr': 4326,  # WGS84
                'layers': 'visible:9',  # Layer 9 = "Lot" (individual properties)
                'tolerance': 1,  # Very tight tolerance - must click directly on property
                'mapExtent': bbox,
                'imageDisplay': '400,400,96',
                'returnGeometry': 'true',
                'f': 'json'
            }
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('results') and len(data['results']) > 0:
                    # Get the first result (the property at this point)
                    property_data = data['results'][0]
                    
                    # Debug: print what property we found
                    attributes = property_data.get('attributes', {})
                    print(f"  Cadastre returned: {attributes.get('lotidstring', 'Unknown lot')}")
                    
                    geometry = property_data.get('geometry', {})
                    rings = geometry.get('rings', [])
                    
                    if rings:
                        # Convert rings to list of tuples
                        # Each ring is [[lng, lat], [lng, lat], ...]
                        polygon_rings = []
                        for ring in rings:
                            # Convert to (lat, lng) tuples for consistency
                            polygon_ring = [(point[1], point[0]) for point in ring]
                            polygon_rings.append(polygon_ring)
                        
                        print(f"  Found NSW cadastral boundary with {len(polygon_rings)} ring(s)")
                        return polygon_rings
                else:
                    print(f"  No cadastral boundary found at this location")
                    return None
            else:
                print(f"  Cadastre API error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"  Error fetching NSW cadastre boundary: {e}")
            return None
    
    def draw_property_boundary_and_marker(self, image_data: bytes, lat: float, lng: float, 
                                          image_center_lat: float, image_center_lng: float) -> bytes:
        """
        Draw property boundary from NSW Cadastre and a red dot marker.
        
        Args:
            image_data: Satellite image bytes
            lat: Property latitude (geocoded address point - used to fetch boundary)
            lng: Property longitude (geocoded address point - used to fetch boundary)
            image_center_lat: Latitude of image center (property centroid)
            image_center_lng: Longitude of image center (property centroid)
            
        Returns:
            Annotated image bytes
        """
        try:
            import math
            
            # Open image
            img = Image.open(BytesIO(image_data))
            
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            draw = ImageDraw.Draw(img)
            img_size = 640
            zoom = 20  # Google Maps zoom level
            
            # Calculate degrees per pixel using Web Mercator projection at image center
            earth_circumference = 40075016.686  # meters at equator
            lat_rad = math.radians(image_center_lat)
            meters_per_pixel = (earth_circumference * math.cos(lat_rad)) / (2 ** (zoom + 8))
            
            # Degrees per pixel
            lat_degrees_per_pixel = meters_per_pixel / 111320.0
            lng_degrees_per_pixel = meters_per_pixel / (111320.0 * math.cos(lat_rad))
            
            # Get property boundary from NSW Cadastre (using geocoded address point)
            boundary_rings = self.get_nsw_property_boundary(lat, lng)
            
            if boundary_rings:
                # Draw each ring (outer boundary and any holes)
                for ring in boundary_rings:
                    pixel_coords = []
                    for point_lat, point_lng in ring:
                        # Calculate offset from IMAGE CENTER (not geocoded point)
                        lat_offset = point_lat - image_center_lat
                        lng_offset = point_lng - image_center_lng
                        
                        # Convert to pixels (y is inverted for image coordinates)
                        x = img_size / 2 + (lng_offset / lng_degrees_per_pixel)
                        y = img_size / 2 - (lat_offset / lat_degrees_per_pixel)
                        
                        pixel_coords.append((int(x), int(y)))
                    
                    # Draw the boundary with thick red line
                    if len(pixel_coords) >= 3:
                        # Draw as a closed polygon outline
                        draw.line(pixel_coords + [pixel_coords[0]], fill='red', width=4)
            else:
                # Fallback: just draw a red dot if no boundary found
                print(f"  Drawing marker only (no boundary data)")
                center_x = img_size / 2
                center_y = img_size / 2
                dot_radius = 15
                
                draw.ellipse(
                    [(center_x - dot_radius, center_y - dot_radius),
                     (center_x + dot_radius, center_y + dot_radius)],
                    fill='red',
                    outline='white',
                    width=2
                )
            
            # Save to bytes
            output = BytesIO()
            img.save(output, format='JPEG')
            return output.getvalue()
            
        except Exception as e:
            print(f"  Error drawing boundary: {e}")
            return image_data  # Return original if drawing fails
    
    def get_streets_in_suburb(self, suburb: str, max_streets: int = 10) -> List[Dict]:
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
        search_url = f"{self.osm_base_url}/search"
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
            overpass_url = "https://overpass-api.de/api/interpreter"
            
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
    
    def find_nearest_house_number(self, lat: float, lon: float, street_name: str, suburb: str) -> Optional[int]:
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
        geocode_url = f"{self.google_maps_base_url}/geocode/json"
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
            
            # If reverse geocoding didn't work, try a few nearby numbers
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
                
                time.sleep(0.1)
            
            return None
            
        except Exception as e:
            print(f"  Error finding nearest house number: {e}")
            return None
        
    def geocode_street(self, street_name: str, suburb: str) -> List[Dict]:
        """
        Find addresses along a street using Google Maps Geocoding API.
        
        Args:
            street_name: Name of the street
            suburb: Suburb or city name
            
        Returns:
            List of address dictionaries with location data
        """
        print(f"\nSearching for addresses on {street_name}, {suburb}...")
        
        # Check if we have existing analysis
        existing_addresses = self.load_existing_addresses(street_name, suburb)
        if existing_addresses:
            return existing_addresses
        
        # Search for the street
        search_query = f"{street_name}, {suburb}"
        geocode_url = f"{self.google_maps_base_url}/geocode/json"
        
        params = {
            'address': search_query,
            'key': GOOGLE_MAPS_API_KEY
        }
        
        response = requests.get(geocode_url, params=params)
        data = response.json()
        
        if data['status'] != 'OK':
            print(f"Error geocoding street: {data['status']}")
            return []
        
        # Get the street's location
        street_location = data['results'][0]['geometry']['location']
        formatted_address = data['results'][0]['formatted_address']
        print(f"Found street: {formatted_address}")
        
        # Enumerate addresses along the street
        addresses = self._enumerate_street_addresses(street_name, suburb, street_location)
        
        return addresses
    
    def _enumerate_street_addresses(self, street_name: str, suburb: str, center_location: Dict, num_addresses: int = 20) -> List[Dict]:
        """
        Enumerate addresses along a street by trying house numbers around the geocentre.
        
        Args:
            street_name: Street name
            suburb: Suburb name
            center_location: Dictionary with 'lat' and 'lng' or 'lon' keys
            num_addresses: Maximum number of addresses to find
            
        Returns:
            List of valid addresses
        """
        addresses = []
        
        # Get lat/lon from center_location (handle both 'lng' and 'lon' keys)
        center_lat = center_location.get('lat')
        center_lon = center_location.get('lon') or center_location.get('lng')
        
        # Find the nearest house number to the geocentre
        print(f"Finding nearest address to street geocentre...")
        nearest_number = self.find_nearest_house_number(center_lat, center_lon, street_name, suburb)
        
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
        attempts = 0
        max_attempts = min(len(house_numbers), num_addresses * 20)  # Try up to 20x the requested amount
        
        for num in house_numbers:
            if found_count >= num_addresses or attempts >= max_attempts:
                break
            
            attempts += 1
            full_address = f"{num} {street_name}, {suburb}"
            
            # Geocode this specific address
            geocode_url = f"{self.google_maps_base_url}/geocode/json"
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
                            # Avoid duplicates
                            if not any(addr['address'] == formatted_addr for addr in addresses):
                                addresses.append({
                                    'address': formatted_addr,
                                    'lat': result['geometry']['location']['lat'],
                                    'lng': result['geometry']['location']['lng']
                                })
                                found_count += 1
                                print(f"  Found: {formatted_addr}")
                    else:
                        print(f"  Skipping {full_address} - location too approximate ({location_type})")
                
                # Small delay to avoid rate limiting
                if attempts % 10 == 0:
                    time.sleep(0.5)
                else:
                    time.sleep(0.1)
                    
            except Exception as e:
                print(f"  Error checking {full_address}: {e}")
                continue
    
        print(f"\nFound {len(addresses)} valid addresses (tried {attempts} house numbers)")
        return addresses

    def save_satellite_image(self, image_data: bytes, street_name: str, suburb: str, 
                           address: str, lat: float, lng: float, image_center_lat: float, image_center_lng: float) -> Tuple[str, bytes]:
        """
        Save satellite image with property marker to street folder.
        
        Args:
            image_data: Image data as bytes
            street_name: Name of the street
            suburb: Suburb name
            address: Full address (used for filename)
            lat: Latitude of property (geocoded address point)
            lng: Longitude of property (geocoded address point)
            image_center_lat: Latitude of the image center (property centroid)
            image_center_lng: Longitude of the image center (property centroid)
            
        Returns:
            Tuple of (filepath, annotated_image_data)
        """
        # Get street folder
        folder_path = self.get_street_folder(street_name, suburb)
        
        # Create folder if it doesn't exist
        os.makedirs(folder_path, exist_ok=True)
        
        # Create safe filename from address (extract house number)
        match = re.match(r'^(\d+)', address)
        if match:
            house_number = match.group(1)
            filename = f"{house_number}.jpg"
        else:
            # Fallback: use sanitized address
            filename = address.replace(' ', '_').replace(',', '').replace('/', '_')[:50] + '.jpg'
        
        filepath = os.path.join(folder_path, filename)
        
        # Draw property boundary and marker on the image
        # Note: image is centered at image_center, boundary is fetched at geocoded (lat, lng)
        annotated_image = self.draw_property_boundary_and_marker(image_data, lat, lng, image_center_lat, image_center_lng)
        
        # Save annotated image
        try:
            with open(filepath, 'wb') as f:
                f.write(annotated_image)
            print(f"  Saved image to: {filepath}")
            return filepath, annotated_image
        except Exception as e:
            print(f"  Error saving image: {e}")
            return filepath, image_data
    
    def get_satellite_image(self, lat: float, lng: float, zoom: int = 20) -> bytes:
        """
        Retrieve satellite imagery for a location using Google Maps Static API.
        
        Args:
            lat: Latitude
            lng: Longitude
            zoom: Zoom level (20 is very close, good for seeing gardens)
            
        Returns:
            Image data as bytes
        """
        static_map_url = f"{self.google_maps_base_url}/staticmap"
        
        params = {
            'center': f"{lat},{lng}",
            'zoom': zoom,
            'size': '640x640',
            'maptype': 'satellite',
            'key': GOOGLE_MAPS_API_KEY
        }
        
        response = requests.get(static_map_url, params=params)
        
        if response.status_code == 200:
            return response.content
        else:
            print(f"Error fetching satellite image: {response.status_code}")
            return None
    
    def analyze_garden_likelihood(self, image_data: bytes, address: str) -> Dict[str, str]:
        """
        Use OpenAI Vision API to analyze an image for vegetable garden presence.
        
        Args:
            image_data: Satellite image as bytes
            address: Address being analyzed (for context)
            
        Returns:
            Dictionary with 'reasoning' and 'likelihood' keys
        """
        import base64
        import json
        
        # Convert image to base64
        base64_image = base64.b64encode(image_data).decode('utf-8')
        
        prompt = """Analyze this satellite/aerial image of a suburban property and determine the likelihood 
that there is a vegetable garden present. You are looking at just one property

IMPORTANT: The property being analyzed is marked with a RED BOUNDARY LINE showing the property borders. 
Focus your analysis on the area within the red boundary.

Look for:
- Organized rows of plants
- Raised garden beds
- Rectangular or organized garden patches
- Dark soil areas with regular patterns
- Areas that appear to be cultivated (different from lawn)

First, provide your reasoning about what you observe in the property. Then, determine the likelihood level.

Likelihood levels:
- low: No clear evidence of a vegetable garden, mostly lawn/pavement/natural vegetation
- medium: Some signs that could be a garden (organized plantings, possible raised beds) but not definitive
- high: Clear evidence of vegetable garden (visible rows, raised beds, organized cultivation)"""
        
        # Define the function schema for structured output
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "analyze_garden",
                    "description": "Analyze a satellite image to determine the likelihood of a vegetable garden being present",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "reasoning": {
                                "type": "string",
                                "description": "Detailed reasoning about what is observed in the property, including visible features, vegetation patterns, and any signs of cultivation or garden structures"
                            },
                            "likelihood": {
                                "type": "string",
                                "enum": ["low", "medium", "high"],
                                "description": "The likelihood level of a vegetable garden being present: low (no clear evidence), medium (some signs but not definitive), or high (clear evidence)"
                            }
                        },
                        "required": ["reasoning", "likelihood"]
                    }
                }
            }
        ]
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                tools=tools,
                tool_choice={"type": "function", "function": {"name": "analyze_garden"}}
            )
            
            # Extract the function call response
            tool_call = response.choices[0].message.tool_calls[0]
            result = json.loads(tool_call.function.arguments)
            
            reasoning = result.get('reasoning', 'No reasoning provided')
            likelihood = result.get('likelihood', 'low').lower()
            
            # Validate the likelihood
            if likelihood not in ['low', 'medium', 'high']:
                print(f"  Unexpected likelihood value: {likelihood}, defaulting to 'low'")
                likelihood = 'low'
            
            return {
                'reasoning': reasoning,
                'likelihood': likelihood
            }
                
        except Exception as e:
            print(f"  Error analyzing image: {e}")
            return {
                'reasoning': 'Error occurred during analysis',
                'likelihood': 'low'
            }
    
    def process_street(self, street_name: str, suburb: str, max_addresses: int = 20) -> List[Dict]:
        """
        Main processing function: find addresses and analyze for gardens.
        
        Args:
            street_name: Name of the street
            suburb: Suburb or city
            max_addresses: Maximum number of addresses to process
            
        Returns:
            List of results with addresses and garden likelihood
        """
        # Get addresses
        addresses = self.geocode_street(street_name, suburb)
        
        if not addresses:
            print("No addresses found.")
            return []
        
        # Limit to max_addresses
        addresses = addresses[:max_addresses]
        
        results = []
        print(f"\nAnalyzing {len(addresses)} addresses for garden likelihood...")
        
        for i, addr_info in enumerate(addresses, 1):
            address = addr_info['address']
            lat = addr_info['lat']
            lng = addr_info['lng']
            
            print(f"\n[{i}/{len(addresses)}] Processing: {address}")
            
            # First, get the property boundary to find the centroid
            print(f"  Fetching property boundary to determine centroid...")
            boundary_rings = self.get_nsw_property_boundary(lat, lng)
            
            # Calculate centroid of property boundary for image centering
            if boundary_rings and len(boundary_rings) > 0:
                # Use the outer ring (first ring) to calculate centroid
                outer_ring = boundary_rings[0]
                centroid_lat = sum(pt[0] for pt in outer_ring) / len(outer_ring)
                centroid_lng = sum(pt[1] for pt in outer_ring) / len(outer_ring)
                print(f"  Property centroid: ({centroid_lat:.6f}, {centroid_lng:.6f})")
            else:
                # Fallback: use geocoded address point if no boundary found
                centroid_lat = lat
                centroid_lng = lng
                print(f"  No boundary found, using geocoded point as center")
            
            # Get satellite image centered on property centroid
            image_data = self.get_satellite_image(centroid_lat, centroid_lng)
            
            if not image_data:
                print(f"  Skipping - could not retrieve image")
                results.append({
                    'address': address,
                    'garden_likelihood': 'unknown',
                    'reasoning': 'Could not retrieve satellite image'
                })
                continue
            
            # Save satellite image with property boundary to street folder
            filepath, annotated_image = self.save_satellite_image(
                image_data, street_name, suburb, address, lat, lng, centroid_lat, centroid_lng
            )
            
            # Analyze for garden using annotated image
            print(f"  Analyzing image with AI...")
            analysis = self.analyze_garden_likelihood(annotated_image, address)
            
            print(f"  Garden likelihood: {analysis['likelihood'].upper()}")
            print(f"  Reasoning: {analysis['reasoning'][:100]}...")  # Print first 100 chars
            
            results.append({
                'address': address,
                'garden_likelihood': analysis['likelihood'],
                'reasoning': analysis['reasoning']
            })
            
            # Rate limiting to avoid API throttling
            time.sleep(1)
        
        self.results = results
        return results
    
    def save_to_csv(self, filename: str = "garden_analysis.csv", street_folder: str = None):
        """
        Save results to a CSV file.
        
        Args:
            filename: Output filename
            street_folder: Specific folder path to save to (if None, saves to current directory)
        """
        if not self.results:
            print("No results to save.")
            return
        
        if street_folder:
            os.makedirs(street_folder, exist_ok=True)
            filepath = os.path.join(street_folder, filename)
        else:
            filepath = os.path.join(os.getcwd(), filename)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['address', 'garden_likelihood', 'reasoning']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for result in self.results:
                writer.writerow(result)
        
        print(f"\n✓ Results saved to: {filepath}")
        print(f"  Total addresses analyzed: {len(self.results)}")
        
        # Print summary statistics
        low = sum(1 for r in self.results if r['garden_likelihood'] == 'low')
        medium = sum(1 for r in self.results if r['garden_likelihood'] == 'medium')
        high = sum(1 for r in self.results if r['garden_likelihood'] == 'high')
        
        print(f"\n  Summary:")
        print(f"    Low likelihood:    {low}")
        print(f"    Medium likelihood: {medium}")
        print(f"    High likelihood:   {high}")


def main():
    """Main entry point for the application."""
    print("=" * 60)
    print("Garden Detection Application")
    print("=" * 60)
    
    # Create detector
    detector = GardenDetector()
    
    # Get user input
    if len(sys.argv) >= 2:
        suburb = sys.argv[1]
        max_addresses = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        max_streets = int(sys.argv[3]) if len(sys.argv) > 3 else 5
        street_name = None
    else:
        mode = input("\nChoose mode:\n  1. Analyze specific street\n  2. Analyze multiple streets in suburb\nEnter choice (1 or 2): ").strip()
        
        if mode == '1':
            # Single street mode
            street_name = input("\nEnter street name: ").strip()
            suburb = input("Enter suburb/city: ").strip()
            max_input = input("Enter max number of addresses to analyze (default 20): ").strip()
            max_addresses = int(max_input) if max_input else 20
            max_streets = 1
        else:
            # Multiple streets mode
            suburb = input("\nEnter suburb/city: ").strip()
            max_input = input("Enter max number of addresses per street (default 20): ").strip()
            max_addresses = int(max_input) if max_input else 20
            streets_input = input("Enter number of streets to analyze (default 5): ").strip()
            max_streets = int(streets_input) if streets_input else 5
            street_name = None
    
    if not suburb:
        print("Error: Suburb is required.")
        sys.exit(1)
    
    try:
        if street_name:
            # Single street mode
            results = detector.process_street(street_name, suburb, max_addresses)
            
            if results:
                # Save to CSV in street folder
                street_folder = detector.get_street_folder(street_name, suburb)
                output_filename = f"garden_analysis_{street_name.replace(' ', '_')}_{suburb.replace(' ', '_')}.csv"
                detector.save_to_csv(output_filename, street_folder)
        else:
            # Multiple streets mode
            streets = detector.get_streets_in_suburb(suburb, max_streets)
            
            if not streets:
                print("No streets found.")
                sys.exit(1)
            
            print(f"\nWill analyze {len(streets)} streets:")
            for i, street in enumerate(streets, 1):
                print(f"  {i}. {street['name']}")
            
            # Process each street
            all_results = []
            for i, street_info in enumerate(streets, 1):
                print(f"\n{'='*60}")
                print(f"Processing street {i}/{len(streets)}: {street_info['name']}")
                print(f"{'='*60}")
                
                # Use OSM geocentre for this street
                center_location = {'lat': street_info['lat'], 'lon': street_info['lon']}
                addresses = detector._enumerate_street_addresses(
                    street_info['name'], 
                    suburb, 
                    center_location, 
                    max_addresses
                )
                
                if not addresses:
                    print(f"No addresses found on {street_info['name']}")
                    continue
                
                # Limit to max_addresses
                addresses = addresses[:max_addresses]
                
                print(f"\nAnalyzing {len(addresses)} addresses on {street_info['name']}...")
                
                for j, addr_info in enumerate(addresses, 1):
                    address = addr_info['address']
                    lat = addr_info['lat']
                    lng = addr_info['lng']
                    
                    print(f"\n[{j}/{len(addresses)}] Processing: {address}")
                    
                    # Get satellite image
                    image_data = detector.get_satellite_image(lat, lng)
                    
                    if not image_data:
                        print(f"  Skipping - could not retrieve image")
                        all_results.append({
                            'address': address,
                            'garden_likelihood': 'unknown',
                            'reasoning': 'Could not retrieve satellite image'
                        })
                        continue
                    
                    # Save satellite image with property boundary to street folder
                    filepath, annotated_image = detector.save_satellite_image(
                        image_data, street_info['name'], suburb, address, lat, lng
                    )
                    
                    # Analyze for garden using annotated image
                    print(f"  Analyzing image with AI...")
                    analysis = detector.analyze_garden_likelihood(annotated_image, address)
                    
                    print(f"  Garden likelihood: {analysis['likelihood'].upper()}")
                    print(f"  Reasoning: {analysis['reasoning'][:100]}...")  # Print first 100 chars
                    
                    all_results.append({
                        'address': address,
                        'garden_likelihood': analysis['likelihood'],
                        'reasoning': analysis['reasoning']
                    })
                    
                    # Rate limiting to avoid API throttling
                    time.sleep(1)
            
            # Save results for each street separately
            if all_results:
                # Group results by street
                from collections import defaultdict
                results_by_street = defaultdict(list)
                
                for result in all_results:
                    # Extract street name from address
                    addr = result['address']
                    for street_info in streets:
                        if street_info['name'].lower() in addr.lower():
                            results_by_street[street_info['name']].append(result)
                            break
                
                # Save CSV for each street
                for street_name, street_results in results_by_street.items():
                    detector.results = street_results
                    street_folder = detector.get_street_folder(street_name, suburb)
                    output_filename = f"garden_analysis_{street_name.replace(' ', '_')}_{suburb.replace(' ', '_')}.csv"
                    detector.save_to_csv(output_filename, street_folder)
        
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
