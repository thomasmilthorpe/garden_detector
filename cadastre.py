"""
NSW Cadastre integration module for Garden Detector application.
Handles fetching and drawing property boundaries from NSW Cadastre MapServer.
"""

import math
import requests
from io import BytesIO
from typing import List, Tuple, Optional
from PIL import Image, ImageDraw
from config import CADASTRE_BASE_URL


def get_nsw_property_boundary(lat: float, lng: float) -> Optional[List[List[Tuple[float, float]]]]:
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
        
        url = f"{CADASTRE_BASE_URL}/identify"
        
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


def draw_property_boundary_and_marker(image_data: bytes, lat: float, lng: float, 
                                      image_center_lat: float, image_center_lng: float,
                                      zoom: int = 20, img_size: int = 640) -> bytes:
    """
    Draw property boundary from NSW Cadastre and a red dot marker on satellite image.
    
    Args:
        image_data: Satellite image bytes
        lat: Property latitude (geocoded address point - used to fetch boundary)
        lng: Property longitude (geocoded address point - used to fetch boundary)
        image_center_lat: Latitude of image center (property centroid)
        image_center_lng: Longitude of image center (property centroid)
        zoom: Google Maps zoom level (default 20)
        img_size: Image size in pixels (default 640)
        
    Returns:
        Annotated image bytes
    """
    try:
        # Open image
        img = Image.open(BytesIO(image_data))
        
        # Convert to RGB if necessary
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        draw = ImageDraw.Draw(img)
        
        # Calculate degrees per pixel using Web Mercator projection at image center
        earth_circumference = 40075016.686  # meters at equator
        lat_rad = math.radians(image_center_lat)
        meters_per_pixel = (earth_circumference * math.cos(lat_rad)) / (2 ** (zoom + 8))
        
        # Degrees per pixel
        lat_degrees_per_pixel = meters_per_pixel / 111320.0
        lng_degrees_per_pixel = meters_per_pixel / (111320.0 * math.cos(lat_rad))
        
        # Get property boundary from NSW Cadastre (using geocoded address point)
        boundary_rings = get_nsw_property_boundary(lat, lng)
        
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
