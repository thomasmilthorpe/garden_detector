# NSW Cadastre MapServer Integration Guide

## Overview

This document provides complete integration instructions for the NSW Cadastre MapServer API, which provides property boundary (cadastral) data for New South Wales, Australia.

**Service URL:** `https://maps.six.nsw.gov.au/arcgis/rest/services/public/NSW_Cadastre/MapServer`

**Provider:** Department of Finance, Services & Innovation (DFSI Spatial Services NSW)

**Purpose:** Retrieve property boundaries to overlay on satellite imagery with red borders for user context.

---

## Table of Contents

1. [Service Capabilities](#service-capabilities)
2. [Setup Requirements](#setup-requirements)
3. [API Endpoints](#api-endpoints)
4. [Common Operations](#common-operations)
5. [Code Examples](#code-examples)
6. [Error Handling](#error-handling)
7. [Best Practices](#best-practices)

---

## Service Capabilities

### What This Service Provides:

- Property boundary geometries (polygons)
- Lot, Plan, and Section information
- Query by coordinates or property identifiers
- Export map images with cadastral overlays
- Multiple image formats (PNG32, PNG24, JPG, etc.)

### Key Specifications:

- **Spatial Reference:** EPSG:3857 (Web Mercator) and EPSG:4326 (WGS84) supported
- **Coverage:** All of New South Wales
- **Max Image Dimensions:** 4096 x 4096 pixels
- **Max Record Count:** 1000 records per query
- **Supported Formats:** JSON, AMF, geoJSON
- **Image Formats:** PNG32, PNG24, PNG, JPG, TIFF, PDF, SVG, BMP

---

## Setup Requirements

### 1. No Authentication Required

This is a public service - no API key or authentication is needed.

### 2. Dependencies

**Required:**
```bash
pip install requests
```

**Optional (for advanced geometry manipulation):**
```bash
pip install shapely
pip install pillow  # For image manipulation
pip install matplotlib  # For drawing borders on images
```

### 3. Coordinate System Understanding

- **Input coordinates:** Can be in WGS84 (EPSG:4326) - standard lat/lng
- **Service native format:** Web Mercator (EPSG:3857)
- Most satellite imagery services use WGS84, so you'll need to specify `sr=4326` in your requests

### 4. Network Requirements

- Outbound HTTPS access to `maps.six.nsw.gov.au`
- No special firewall rules needed for public services

---

## API Endpoints

### Base URL
```
https://maps.six.nsw.gov.au/arcgis/rest/services/public/NSW_Cadastre/MapServer
```

### 1. Service Metadata
**Endpoint:** `/`  
**Method:** GET  
**Description:** Get service information, available layers, and capabilities

**Parameters:**
- `f` - Response format (json, html, pjson)

**Example:**
```
https://maps.six.nsw.gov.au/arcgis/rest/services/public/NSW_Cadastre/MapServer?f=json
```

---

### 2. Identify (Query by Point)
**Endpoint:** `/identify`  
**Method:** GET  
**Description:** Find property boundaries at a specific location

**Required Parameters:**
- `geometry` - Point coordinates (longitude,latitude)
- `geometryType` - Type of geometry (esriGeometryPoint)
- `sr` - Spatial reference (4326 for WGS84)
- `layers` - Which layers to query (all:0 or all)
- `tolerance` - Search tolerance in pixels
- `mapExtent` - Bounding box of map area (minX,minY,maxX,maxY)
- `imageDisplay` - Display dimensions (width,height,dpi)
- `returnGeometry` - Return geometry data (true/false)
- `f` - Response format (json, geojson)

**Optional Parameters:**
- `layerDefs` - Layer definition expressions for filtering
- `time` - Time instant or time extent
- `returnFieldName` - Return field names instead of aliases
- `returnUnformattedValues` - Return unformatted values

**Example:**
```
https://maps.six.nsw.gov.au/arcgis/rest/services/public/NSW_Cadastre/MapServer/identify?
geometry=146.9166,-36.0833&
geometryType=esriGeometryPoint&
sr=4326&
layers=all&
tolerance=5&
mapExtent=146.91,-36.09,146.92,-36.08&
imageDisplay=400,400,96&
returnGeometry=true&
f=json
```

---

### 3. Find (Search by Attributes)
**Endpoint:** `/find`  
**Method:** GET  
**Description:** Search for properties by lot number, plan number, or other attributes

**Required Parameters:**
- `searchText` - Text to search for
- `contains` - Whether search text should be contained (true) or exact match (false)
- `searchFields` - Comma-separated list of field names to search
- `sr` - Spatial reference for returned geometries
- `f` - Response format (json, geojson)

**Optional Parameters:**
- `layers` - Comma-separated list of layer IDs to search
- `returnGeometry` - Return geometry data (true/false)

**Example:**
```
https://maps.six.nsw.gov.au/arcgis/rest/services/public/NSW_Cadastre/MapServer/find?
searchText=LOT 1&
contains=true&
searchFields=&
sr=4326&
layers=&
returnGeometry=true&
f=json
```

---

### 4. Export Map
**Endpoint:** `/export`  
**Method:** GET  
**Description:** Generate a map image with cadastral boundaries

**Required Parameters:**
- `bbox` - Bounding box (minX,minY,maxX,maxY)
- `bboxSR` - Spatial reference of bounding box (4326 for WGS84)
- `size` - Image dimensions (width,height) - max 4096x4096
- `imageSR` - Spatial reference for output image
- `format` - Image format (png, png32, jpg, pdf, etc.)
- `f` - Response format (json, image, html)

**Optional Parameters:**
- `layers` - Control which layers to display
- `layerDefs` - Filter features on specific layers
- `transparent` - Whether background is transparent (true/false)
- `dpi` - Dots per inch (default 96)
- `time` - Time instant or extent

**Example:**
```
https://maps.six.nsw.gov.au/arcgis/rest/services/public/NSW_Cadastre/MapServer/export?
bbox=146.91,-36.09,146.92,-36.08&
bboxSR=4326&
size=800,600&
imageSR=4326&
format=png32&
transparent=true&
f=image
```

---

### 5. Query Layer
**Endpoint:** `/{layerId}/query`  
**Method:** GET  
**Description:** Advanced queries on specific layers

**Note:** First, you need to determine the layer ID. Use the service metadata endpoint to get layer information.

**Key Parameters:**
- `where` - SQL where clause (e.g., "OBJECTID > 0")
- `geometry` - Geometry to query (polygon, point, etc.)
- `geometryType` - Type of geometry
- `spatialRel` - Spatial relationship (esriSpatialRelIntersects, etc.)
- `outFields` - Fields to return (comma-separated or "*" for all)
- `returnGeometry` - Return geometry (true/false)
- `f` - Response format (json, geojson)

**Example:**
```
https://maps.six.nsw.gov.au/arcgis/rest/services/public/NSW_Cadastre/MapServer/0/query?
where=OBJECTID>0&
geometry=146.9166,-36.0833&
geometryType=esriGeometryPoint&
spatialRel=esriSpatialRelIntersects&
outFields=*&
returnGeometry=true&
f=json
```

---

## Common Operations

### Operation 1: Get Property Boundary at Coordinates

**Use Case:** User clicks on a location, you need the property boundary polygon.

**Workflow:**
1. Use the `/identify` endpoint with point coordinates
2. Parse the returned geometry (polygon rings)
3. Use the polygon to draw borders on your map/image

**Required Data:**
- Latitude and longitude of point
- Approximate map extent around the point

---

### Operation 2: Export Cadastral Layer as Transparent Overlay

**Use Case:** Create a transparent PNG of property boundaries to overlay on satellite imagery.

**Workflow:**
1. Use the `/export` endpoint with your bounding box
2. Set `transparent=true` and `format=png32`
3. Overlay the returned image on your satellite imagery

**Required Data:**
- Bounding box of area of interest
- Desired image dimensions

---

### Operation 3: Search for Specific Property

**Use Case:** User searches for "Lot 5 DP 123456"

**Workflow:**
1. Use the `/find` endpoint with search text
2. Parse returned results for matching properties
3. Extract geometry for the desired property

**Required Data:**
- Property identifier (lot number, plan number, etc.)

---

## Code Examples

### Example 1: Get Property Boundary at Coordinates

```python
import requests
import json

def get_property_boundary(longitude, latitude):
    """
    Get property boundary polygon at given coordinates.
    
    Args:
        longitude (float): Longitude in decimal degrees (e.g., 146.9166 for Albury)
        latitude (float): Latitude in decimal degrees (e.g., -36.0833 for Albury)
    
    Returns:
        dict: Property attributes and boundary geometry, or None if not found
    """
    # Create bounding box around the point (roughly 500m radius)
    offset = 0.005  # approximately 500m
    bbox = f"{longitude - offset},{latitude - offset},{longitude + offset},{latitude + offset}"
    
    url = "https://maps.six.nsw.gov.au/arcgis/rest/services/public/NSW_Cadastre/MapServer/identify"
    
    params = {
        'geometry': f"{longitude},{latitude}",
        'geometryType': 'esriGeometryPoint',
        'sr': 4326,
        'layers': 'all',
        'tolerance': 5,
        'mapExtent': bbox,
        'imageDisplay': '400,400,96',
        'returnGeometry': 'true',
        'f': 'json'
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('results') and len(data['results']) > 0:
            property_data = data['results'][0]
            geometry = property_data.get('geometry')
            attributes = property_data.get('attributes')
            
            print(f"Property found: {attributes}")
            print(f"Boundary polygon rings: {len(geometry.get('rings', []))} ring(s)")
            
            return {
                'attributes': attributes,
                'polygon': geometry.get('rings'),  # List of coordinate rings
                'geometry': geometry
            }
        else:
            print("No property found at this location")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Error querying cadastre: {e}")
        raise

# Usage example
if __name__ == "__main__":
    # Coordinates for a location in Albury, NSW
    result = get_property_boundary(146.9166, -36.0833)
    
    if result:
        print("Successfully retrieved property boundary")
        print(f"Number of polygon rings: {len(result['polygon'])}")
        # Use result['polygon'] to draw red borders on your satellite image
```

---

### Example 2: Export Cadastral Map as Transparent PNG

```python
import requests

def export_cadastre_map(bbox, output_path, width=1024, height=768):
    """
    Export cadastral boundaries as a transparent PNG image.
    
    Args:
        bbox (str): Bounding box 'minLon,minLat,maxLon,maxLat'
        output_path (str): Path to save the output image
        width (int): Image width in pixels (max 4096)
        height (int): Image height in pixels (max 4096)
    
    Returns:
        str: Path to saved image
    """
    url = "https://maps.six.nsw.gov.au/arcgis/rest/services/public/NSW_Cadastre/MapServer/export"
    
    params = {
        'bbox': bbox,
        'bboxSR': 4326,
        'size': f"{width},{height}",
        'imageSR': 4326,
        'format': 'png32',
        'transparent': 'true',
        'f': 'image',
        'layers': 'show:0'  # Adjust based on available layers
    }
    
    try:
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()
        
        # Save the image
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        print(f"Map exported to {output_path}")
        return output_path
        
    except requests.exceptions.RequestException as e:
        print(f"Error exporting map: {e}")
        raise

# Usage example
if __name__ == "__main__":
    # Bounding box for an area in Albury, NSW
    bbox = '146.91,-36.09,146.92,-36.08'
    export_cadastre_map(bbox, 'cadastre_overlay.png')
```

---

### Example 3: Search for Property by Lot Number

```python
import requests

def find_property(search_text, return_geometry=True):
    """
    Search for properties by lot number, plan number, or other attributes.
    
    Args:
        search_text (str): Text to search for (e.g., "LOT 1", "DP 123456")
        return_geometry (bool): Whether to return geometry data
    
    Returns:
        list: List of matching properties with attributes and geometry
    """
    url = "https://maps.six.nsw.gov.au/arcgis/rest/services/public/NSW_Cadastre/MapServer/find"
    
    params = {
        'searchText': search_text,
        'contains': 'true',
        'searchFields': '',  # Empty searches all fields
        'sr': 4326,
        'layers': '',  # Empty searches all layers
        'returnGeometry': str(return_geometry).lower(),
        'f': 'json'
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        results = data.get('results', [])
        
        print(f"Found {len(results)} matching properties")
        
        properties = []
        for result in results:
            property_data = {
                'attributes': result.get('attributes'),
                'layer_name': result.get('layerName'),
                'geometry': result.get('geometry') if return_geometry else None
            }
            properties.append(property_data)
        
        return properties
        
    except requests.exceptions.RequestException as e:
        print(f"Error searching for property: {e}")
        raise

# Usage example
if __name__ == "__main__":
    properties = find_property("LOT 1")
    
    for prop in properties[:5]:  # Show first 5 results
        print(f"\nProperty: {prop['attributes']}")
        print(f"Layer: {prop['layer_name']}")
```

---

### Example 4: Draw Red Border on Satellite Image

```python
import requests
from PIL import Image, ImageDraw
import io

def draw_property_border_on_image(satellite_image_path, polygon_rings, output_path, border_color='red', border_width=3):
    """
    Draw property boundaries on a satellite image.
    
    Args:
        satellite_image_path (str): Path to satellite image
        polygon_rings (list): List of polygon rings from cadastre API
        output_path (str): Path to save output image
        border_color (str): Color for the border
        border_width (int): Width of the border in pixels
    
    Returns:
        str: Path to output image
    """
    # Open the satellite image
    img = Image.open(satellite_image_path)
    draw = ImageDraw.Draw(img)
    
    # Draw each ring (outer boundary and any holes)
    for ring in polygon_rings:
        # Convert coordinates to pixel coordinates
        # Note: You'll need to map lat/lon to image pixel coordinates
        # This assumes the image covers the exact same extent as the polygon
        # In production, you'd need proper coordinate transformation
        
        # Ring is a list of [lon, lat] pairs
        # Convert to list of tuples for PIL
        points = [(x, y) for x, y in ring]
        
        # Draw the polygon outline
        if len(points) > 2:
            draw.line(points + [points[0]], fill=border_color, width=border_width)
    
    # Save the result
    img.save(output_path)
    print(f"Image with borders saved to {output_path}")
    return output_path

# Usage example combining boundary retrieval and drawing
if __name__ == "__main__":
    # 1. Get property boundary
    result = get_property_boundary(146.9166, -36.0833)
    
    if result and result['polygon']:
        # 2. Assuming you have a satellite image
        satellite_image = 'satellite.jpg'
        output_image = 'property_with_border.jpg'
        
        # 3. Draw red borders
        draw_property_border_on_image(
            satellite_image,
            result['polygon'],
            output_image,
            border_color='red',
            border_width=5
        )
```

---

### Example 5: Complete Integration - Coordinate to Bordered Image

```python
import requests
from PIL import Image, ImageDraw
from io import BytesIO

class CadastreService:
    """
    Complete service class for NSW Cadastre integration.
    """
    
    BASE_URL = "https://maps.six.nsw.gov.au/arcgis/rest/services/public/NSW_Cadastre/MapServer"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'PropertyBorderApp/1.0'})
    
    def get_property_at_point(self, longitude, latitude, tolerance=5):
        """Get property boundary at specific coordinates."""
        offset = 0.005
        bbox = f"{longitude - offset},{latitude - offset},{longitude + offset},{latitude + offset}"
        
        url = f"{self.BASE_URL}/identify"
        params = {
            'geometry': f"{longitude},{latitude}",
            'geometryType': 'esriGeometryPoint',
            'sr': 4326,
            'layers': 'all',
            'tolerance': tolerance,
            'mapExtent': bbox,
            'imageDisplay': '400,400,96',
            'returnGeometry': 'true',
            'f': 'json'
        }
        
        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if data.get('results'):
            return data['results'][0]
        return None
    
    def export_map_image(self, bbox, width=1024, height=768, transparent=True):
        """Export cadastral map as image."""
        url = f"{self.BASE_URL}/export"
        params = {
            'bbox': bbox,
            'bboxSR': 4326,
            'size': f"{width},{height}",
            'imageSR': 4326,
            'format': 'png32' if transparent else 'png24',
            'transparent': str(transparent).lower(),
            'f': 'image'
        }
        
        response = self.session.get(url, params=params, timeout=60)
        response.raise_for_status()
        
        return Image.open(BytesIO(response.content))
    
    def create_property_image_with_border(self, longitude, latitude, 
                                         satellite_image, border_color='red', 
                                         border_width=5):
        """
        Complete workflow: Get property boundary and draw on satellite image.
        
        Args:
            longitude (float): Property longitude
            latitude (float): Property latitude
            satellite_image: PIL Image object or path to satellite image
            border_color (str): Border color
            border_width (int): Border width in pixels
        
        Returns:
            PIL.Image: Image with property border drawn
        """
        # Get property boundary
        property_data = self.get_property_at_point(longitude, latitude)
        
        if not property_data:
            raise ValueError(f"No property found at {longitude}, {latitude}")
        
        # Load satellite image if path provided
        if isinstance(satellite_image, str):
            satellite_image = Image.open(satellite_image)
        else:
            satellite_image = satellite_image.copy()
        
        # Get polygon rings
        geometry = property_data.get('geometry', {})
        rings = geometry.get('rings', [])
        
        if not rings:
            raise ValueError("No geometry data found for property")
        
        # Draw borders
        draw = ImageDraw.Draw(satellite_image)
        
        for ring in rings:
            # Note: In production, you need proper coordinate-to-pixel transformation
            # This is a simplified example
            points = [(lon, lat) for lon, lat in ring]
            
            if len(points) > 2:
                # Draw polygon outline
                draw.line(points + [points[0]], fill=border_color, width=border_width)
        
        return satellite_image

# Usage example
if __name__ == "__main__":
    service = CadastreService()
    
    # Get property information
    property_data = service.get_property_at_point(146.9166, -36.0833)
    
    if property_data:
        print("Property Attributes:")
        for key, value in property_data.get('attributes', {}).items():
            print(f"  {key}: {value}")
        
        # Export cadastral overlay
        bbox = '146.91,-36.09,146.92,-36.08'
        cadastre_overlay = service.export_map_image(bbox)
        cadastre_overlay.save('cadastre_overlay.png')
        print("Cadastral overlay saved")
```

---

### Example 6: Batch Processing Multiple Properties

```python
import requests
import json
import time
from typing import List, Dict

def batch_get_properties(coordinates_list: List[tuple], delay=0.5):
    """
    Get property boundaries for multiple coordinates.
    
    Args:
        coordinates_list: List of (longitude, latitude) tuples
        delay: Delay between requests in seconds (rate limiting)
    
    Returns:
        list: List of property data dictionaries
    """
    url = "https://maps.six.nsw.gov.au/arcgis/rest/services/public/NSW_Cadastre/MapServer/identify"
    results = []
    
    for i, (lon, lat) in enumerate(coordinates_list):
        print(f"Processing property {i+1}/{len(coordinates_list)}: ({lon}, {lat})")
        
        offset = 0.005
        bbox = f"{lon - offset},{lat - offset},{lon + offset},{lat + offset}"
        
        params = {
            'geometry': f"{lon},{lat}",
            'geometryType': 'esriGeometryPoint',
            'sr': 4326,
            'layers': 'all',
            'tolerance': 5,
            'mapExtent': bbox,
            'imageDisplay': '400,400,96',
            'returnGeometry': 'true',
            'f': 'json'
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if data.get('results'):
                results.append({
                    'coordinates': (lon, lat),
                    'property': data['results'][0]
                })
            else:
                results.append({
                    'coordinates': (lon, lat),
                    'property': None
                })
        
        except Exception as e:
            print(f"Error processing ({lon}, {lat}): {e}")
            results.append({
                'coordinates': (lon, lat),
                'error': str(e)
            })
        
        # Rate limiting
        if i < len(coordinates_list) - 1:
            time.sleep(delay)
    
    return results

# Usage example
if __name__ == "__main__":
    # List of properties in Albury area
    coords = [
        (146.9166, -36.0833),
        (146.9200, -36.0850),
        (146.9150, -36.0800)
    ]
    
    properties = batch_get_properties(coords)
    
    # Save results
    with open('batch_properties.json', 'w') as f:
        json.dump(properties, f, indent=2)
    
    print(f"\nProcessed {len(properties)} properties")
    print(f"Successful: {sum(1 for p in properties if p.get('property'))}")
    print(f"Not found: {sum(1 for p in properties if p.get('property') is None)}")
    print(f"Errors: {sum(1 for p in properties if p.get('error'))}")
```

---

## Error Handling

### Common Errors and Solutions

#### 1. HTTP 400 Bad Request
**Cause:** Invalid parameters or malformed request

**Solution:**
```python
try:
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 400:
        print(f"Bad request - check parameters: {params}")
        print(f"Response: {e.response.text}")
    raise
```

**Common causes:**
- Invalid spatial reference code
- Bounding box coordinates in wrong order (should be minX,minY,maxX,maxY)
- Image dimensions exceeding 4096x4096
- Invalid geometry format

#### 2. HTTP 500 Internal Server Error
**Cause:** Server-side processing error

**Solution:**
```python
import time

def retry_request(url, params, max_retries=3, delay=2):
    """Retry request with exponential backoff."""
    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 500:
                if attempt < max_retries - 1:
                    wait_time = delay * (2 ** attempt)
                    print(f"Server error, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise
            else:
                raise
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                print(f"Timeout, retrying...")
                time.sleep(delay)
            else:
                raise
```

#### 3. No Results Returned
**Cause:** No property found at specified location

**Solution:**
```python
def get_property_with_fallback(longitude, latitude, max_tolerance=20):
    """Try increasing tolerance if no results found."""
    for tolerance in [5, 10, 15, 20]:
        if tolerance > max_tolerance:
            break
            
        result = get_property_boundary_with_tolerance(longitude, latitude, tolerance)
        
        if result:
            print(f"Found property with tolerance: {tolerance}")
            return result
    
    print("No property found even with increased tolerance")
    return None
```

#### 4. Timeout Errors
**Cause:** Large bounding box or slow network

**Solution:**
```python
# Increase timeout for large requests
response = requests.get(url, params=params, timeout=60)

# Or split large areas into smaller tiles
def split_bbox_into_tiles(bbox_str, num_tiles=4):
    """Split large bounding box into smaller tiles."""
    minX, minY, maxX, maxY = map(float, bbox_str.split(','))
    
    # Calculate tile dimensions
    width = (maxX - minX) / num_tiles
    height = (maxY - minY) / num_tiles
    
    tiles = []
    for i in range(num_tiles):
        for j in range(num_tiles):
            tile_bbox = (
                minX + i * width,
                minY + j * height,
                minX + (i + 1) * width,
                minY + (j + 1) * height
            )
            tiles.append(','.join(map(str, tile_bbox)))
    
    return tiles
```

#### 5. JSON Parsing Errors
**Cause:** Unexpected response format

**Solution:**
```python
try:
    data = response.json()
except json.JSONDecodeError as e:
    print(f"Failed to parse JSON response")
    print(f"Response status: {response.status_code}")
    print(f"Response content: {response.text[:500]}")  # First 500 chars
    raise
```

### Comprehensive Error Handler

```python
import requests
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CadastreAPIError(Exception):
    """Custom exception for Cadastre API errors."""
    pass

def safe_api_call(url, params, max_retries=3, timeout=30):
    """
    Make API call with comprehensive error handling.
    
    Args:
        url (str): API endpoint URL
        params (dict): Query parameters
        max_retries (int): Maximum number of retry attempts
        timeout (int): Request timeout in seconds
    
    Returns:
        dict: JSON response data
    
    Raises:
        CadastreAPIError: If request fails after all retries
    """
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempt {attempt + 1}/{max_retries}: {url}")
            
            response = requests.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            
            # Parse JSON
            data = response.json()
            
            # Check for API-level errors
            if 'error' in data:
                error_msg = data['error'].get('message', 'Unknown error')
                raise CadastreAPIError(f"API Error: {error_msg}")
            
            logger.info("Request successful")
            return data
            
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout on attempt {attempt + 1}")
            if attempt == max_retries - 1:
                raise CadastreAPIError("Request timed out after all retries")
            time.sleep(2 ** attempt)
            
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code
            
            if status_code == 400:
                # Bad request - don't retry
                logger.error(f"Bad request: {e.response.text[:200]}")
                raise CadastreAPIError(f"Invalid request parameters: {e}")
                
            elif status_code == 500:
                # Server error - retry with backoff
                logger.warning(f"Server error on attempt {attempt + 1}")
                if attempt == max_retries - 1:
                    raise CadastreAPIError("Server error after all retries")
                time.sleep(2 ** attempt)
                
            elif status_code == 503:
                # Service unavailable - retry
                logger.warning(f"Service unavailable on attempt {attempt + 1}")
                if attempt == max_retries - 1:
                    raise CadastreAPIError("Service unavailable after all retries")
                time.sleep(5)
                
            else:
                # Other HTTP error - don't retry
                raise CadastreAPIError(f"HTTP {status_code}: {e}")
                
        except requests.exceptions.ConnectionError:
            logger.error("Connection error - check network connectivity")
            if attempt == max_retries - 1:
                raise CadastreAPIError("Connection failed after all retries")
            time.sleep(2 ** attempt)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise CadastreAPIError(f"Request failed: {e}")
    
    raise CadastreAPIError("Max retries exceeded")
```

---

## Best Practices

### 1. Rate Limiting

The service doesn't explicitly document rate limits, but it's good practice to implement rate limiting:

```python
import time
from datetime import datetime, timedelta

class RateLimiter:
    """Simple rate limiter for API calls."""
    
    def __init__(self, calls_per_minute=30):
        self.calls_per_minute = calls_per_minute
        self.calls = []
    
    def wait_if_needed(self):
        """Wait if rate limit would be exceeded."""
        now = datetime.now()
        
        # Remove calls older than 1 minute
        self.calls = [call_time for call_time in self.calls 
                      if now - call_time < timedelta(minutes=1)]
        
        if len(self.calls) >= self.calls_per_minute:
            # Calculate wait time
            oldest_call = min(self.calls)
            wait_seconds = 60 - (now - oldest_call).total_seconds()
            
            if wait_seconds > 0:
                print(f"Rate limit reached, waiting {wait_seconds:.1f}s")
                time.sleep(wait_seconds)
        
        self.calls.append(now)

# Usage
rate_limiter = RateLimiter(calls_per_minute=30)

for coord in coordinates:
    rate_limiter.wait_if_needed()
    result = get_property_boundary(*coord)
```

### 2. Caching Results

Cache property boundary data to avoid repeated API calls:

```python
import json
import hashlib
from pathlib import Path

class PropertyCache:
    """Cache for property boundary data."""
    
    def __init__(self, cache_dir='./cache'):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
    
    def _get_cache_key(self, longitude, latitude):
        """Generate cache key from coordinates."""
        # Round to 6 decimal places (~0.1m precision)
        key = f"{longitude:.6f},{latitude:.6f}"
        return hashlib.md5(key.encode()).hexdigest()
    
    def get(self, longitude, latitude):
        """Get cached property data."""
        cache_file = self.cache_dir / f"{self._get_cache_key(longitude, latitude)}.json"
        
        if cache_file.exists():
            with open(cache_file, 'r') as f:
                return json.load(f)
        return None
    
    def set(self, longitude, latitude, data):
        """Cache property data."""
        cache_file = self.cache_dir / f"{self._get_cache_key(longitude, latitude)}.json"
        
        with open(cache_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def clear(self):
        """Clear all cached data."""
        for cache_file in self.cache_dir.glob('*.json'):
            cache_file.unlink()

# Usage
cache = PropertyCache()

def get_property_with_cache(longitude, latitude):
    """Get property with caching."""
    # Check cache first
    cached_data = cache.get(longitude, latitude)
    if cached_data:
        print("Using cached data")
        return cached_data
    
    # Fetch from API
    data = get_property_boundary(longitude, latitude)
    
    # Cache the result
    if data:
        cache.set(longitude, latitude, data)
    
    return data
```

### 3. Coordinate Validation

Always validate coordinates before making API calls:

```python
def validate_nsw_coordinates(longitude, latitude):
    """
    Validate that coordinates are within NSW bounds.
    
    NSW approximate bounds:
    - Longitude: 141.0°E to 154.0°E
    - Latitude: -37.5°S to -28.0°S
    """
    if not (141.0 <= longitude <= 154.0):
        raise ValueError(f"Longitude {longitude} outside NSW bounds (141-154)")
    
    if not (-37.5 <= latitude <= -28.0):
        raise ValueError(f"Latitude {latitude} outside NSW bounds (-37.5 to -28)")
    
    return True

# Usage
try:
    validate_nsw_coordinates(longitude, latitude)
    result = get_property_boundary(longitude, latitude)
except ValueError as e:
    print(f"Invalid coordinates: {e}")
```

### 4. Coordinate Transformation

Properly transform coordinates between coordinate systems:

```python
from shapely.geometry import Polygon, Point
from shapely.ops import transform
import pyproj

def transform_coordinates(geometry, from_crs='EPSG:4326', to_crs='EPSG:3857'):
    """
    Transform coordinates between coordinate reference systems.
    
    Args:
        geometry: Shapely geometry object
        from_crs: Source CRS (default WGS84)
        to_crs: Target CRS (default Web Mercator)
    
    Returns:
        Transformed geometry
    """
    project = pyproj.Transformer.from_crs(
        from_crs, to_crs, always_xy=True
    ).transform
    
    return transform(project, geometry)

# Usage example
from shapely.geometry import Polygon

# Property polygon in WGS84
rings = result['polygon']
polygon_wgs84 = Polygon(rings[0])

# Transform to Web Mercator for distance calculations
polygon_mercator = transform_coordinates(polygon_wgs84)
area_sqm = polygon_mercator.area
```

### 5. Logging and Monitoring

Implement comprehensive logging:

```python
import logging
from logging.handlers import RotatingFileHandler

def setup_logging(log_file='cadastre_api.log'):
    """Set up logging configuration."""
    logger = logging.getLogger('cadastre_api')
    logger.setLevel(logging.INFO)
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Usage
logger = setup_logging()

def get_property_with_logging(longitude, latitude):
    """Get property with comprehensive logging."""
    logger.info(f"Requesting property at ({longitude}, {latitude})")
    
    try:
        result = get_property_boundary(longitude, latitude)
        
        if result:
            logger.info(f"Property found: {result['attributes']}")
        else:
            logger.warning(f"No property found at ({longitude}, {latitude})")
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting property: {e}", exc_info=True)
        raise
```

### 6. Image Coordinate Mapping

Properly map geographic coordinates to image pixels:

```python
def create_coordinate_mapper(bbox, image_width, image_height):
    """
    Create a function to map lon/lat to image pixel coordinates.
    
    Args:
        bbox (str): Bounding box 'minLon,minLat,maxLon,maxLat'
        image_width (int): Image width in pixels
        image_height (int): Image height in pixels
    
    Returns:
        function: Mapper function (lon, lat) -> (x, y)
    """
    minLon, minLat, maxLon, maxLat = map(float, bbox.split(','))
    
    lon_range = maxLon - minLon
    lat_range = maxLat - minLat
    
    def map_coord(lon, lat):
        """Map geographic coordinate to pixel coordinate."""
        x = ((lon - minLon) / lon_range) * image_width
        # Y is inverted in image coordinates
        y = ((maxLat - lat) / lat_range) * image_height
        return (int(x), int(y))
    
    return map_coord

# Usage
bbox = '146.91,-36.09,146.92,-36.08'
mapper = create_coordinate_mapper(bbox, 1024, 768)

# Convert property boundary to pixel coordinates
pixel_coords = [mapper(lon, lat) for lon, lat in property_rings[0]]
```

### 7. Performance Optimization

Optimize for multiple property queries:

```python
import concurrent.futures

def get_properties_parallel(coordinates_list, max_workers=5):
    """
    Get multiple properties in parallel.
    
    Args:
        coordinates_list: List of (lon, lat) tuples
        max_workers: Maximum concurrent requests
    
    Returns:
        list: Property data for each coordinate
    """
    def fetch_single(coords):
        lon, lat = coords
        try:
            return get_property_boundary(lon, lat)
        except Exception as e:
            logger.error(f"Error fetching ({lon}, {lat}): {e}")
            return None
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(fetch_single, coordinates_list))
    
    return results

# Usage
coords = [(146.9166, -36.0833), (146.9200, -36.0850)]
properties = get_properties_parallel(coords, max_workers=3)
```

---

## Summary

This NSW Cadastre MapServer integration provides:

1. **Property boundary data** for all of NSW
2. **Multiple query methods** (point, search, export)
3. **Flexible output formats** (JSON, images)
4. **No authentication required**

### Quick Start Checklist

- [ ] Install Python dependencies (`requests`, `Pillow`)
- [ ] Test basic property query with known coordinates
- [ ] Implement error handling and retries
- [ ] Add caching for frequently accessed properties
- [ ] Implement coordinate validation
- [ ] Set up logging
- [ ] Test image overlay generation
- [ ] Implement rate limiting for production use

### Support and Resources

- **Service Documentation:** Access via the base URL with `?f=html`
- **Layer Information:** Check `/layers?f=json` endpoint
- **ArcGIS REST API Docs:** https://developers.arcgis.com/rest/

### Need Help?

Common troubleshooting steps:
1. Verify coordinates are within NSW bounds
2. Check spatial reference matches (4326 vs 3857)
3. Ensure bounding box is in correct order (minX, minY, maxX, maxY)
4. Try reducing image dimensions if getting errors
5. Check network connectivity to maps.six.nsw.gov.au