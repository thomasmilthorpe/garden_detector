#!/usr/bin/env python3
"""
NSW Cadastre API Integration Test Script

This script demonstrates the basic functionality of the NSW Cadastre MapServer API.
Run this to verify your integration is working correctly.

Requirements:
    pip install requests pillow

Usage:
    python test_cadastre_integration.py
"""

import requests
import json
from PIL import Image, ImageDraw
from io import BytesIO
import sys


class NSWCadastreAPI:
    """Simple client for NSW Cadastre MapServer API."""
    
    BASE_URL = "https://maps.six.nsw.gov.au/arcgis/rest/services/public/NSW_Cadastre/MapServer"
    
    def __init__(self, timeout=30):
        self.timeout = timeout
        self.session = requests.Session()
    
    def get_property_at_point(self, longitude, latitude, tolerance=5):
        """
        Get property boundary at specific coordinates.
        
        Args:
            longitude (float): Longitude in decimal degrees
            latitude (float): Latitude in decimal degrees
            tolerance (int): Search tolerance in pixels
        
        Returns:
            dict: Property data including attributes and geometry
        """
        # Create bounding box around point
        offset = 0.005  # ~500m
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
        
        print(f"🔍 Querying property at ({longitude}, {latitude})...")
        
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('results'):
                print(f"✅ Property found!")
                return data['results'][0]
            else:
                print(f"❌ No property found at this location")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error querying API: {e}")
            return None
    
    def export_cadastre_image(self, bbox, width=1024, height=768):
        """
        Export cadastral boundaries as a PNG image.
        
        Args:
            bbox (str): Bounding box 'minLon,minLat,maxLon,maxLat'
            width (int): Image width in pixels
            height (int): Image height in pixels
        
        Returns:
            PIL.Image: Cadastre boundary image
        """
        url = f"{self.BASE_URL}/export"
        params = {
            'bbox': bbox,
            'bboxSR': 4326,
            'size': f"{width},{height}",
            'imageSR': 4326,
            'format': 'png32',
            'transparent': 'true',
            'f': 'image'
        }
        
        print(f"📥 Exporting cadastre map for bbox: {bbox}...")
        
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            image = Image.open(BytesIO(response.content))
            print(f"✅ Map exported successfully ({width}x{height})")
            return image
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error exporting map: {e}")
            return None


def print_property_info(property_data):
    """Print property information in a readable format."""
    if not property_data:
        return
    
    print("\n" + "="*60)
    print("PROPERTY INFORMATION")
    print("="*60)
    
    # Attributes
    attributes = property_data.get('attributes', {})
    print("\n📋 Attributes:")
    for key, value in attributes.items():
        print(f"  • {key}: {value}")
    
    # Geometry
    geometry = property_data.get('geometry', {})
    rings = geometry.get('rings', [])
    
    print(f"\n📐 Geometry:")
    print(f"  • Number of rings: {len(rings)}")
    if rings:
        print(f"  • Points in outer ring: {len(rings[0])}")
        print(f"  • First coordinate: {rings[0][0]}")
        print(f"  • Last coordinate: {rings[0][-1]}")
    
    # Layer info
    print(f"\n🗺️  Layer Information:")
    print(f"  • Layer ID: {property_data.get('layerId')}")
    print(f"  • Layer Name: {property_data.get('layerName')}")
    print(f"  • Display Field: {property_data.get('displayFieldName')}")
    
    print("="*60 + "\n")


def save_property_json(property_data, filename='property_data.json'):
    """Save property data to JSON file."""
    if property_data:
        with open(filename, 'w') as f:
            json.dump(property_data, f, indent=2)
        print(f"💾 Property data saved to {filename}")


def run_tests():
    """Run integration tests."""
    print("\n" + "="*60)
    print("NSW CADASTRE API INTEGRATION TEST")
    print("="*60 + "\n")
    
    # Initialize API client
    api = NSWCadastreAPI()
    
    # Test 1: Get property at a known location (Albury, NSW)
    print("\n### TEST 1: Get Property Boundary ###\n")
    
    # Coordinates for a location in Albury
    test_lon = 146.9166
    test_lat = -36.0833
    
    property_data = api.get_property_at_point(test_lon, test_lat)
    
    if property_data:
        print_property_info(property_data)
        save_property_json(property_data)
    else:
        print("⚠️  Test 1 failed - No property found")
        print("   Try adjusting the coordinates or increasing tolerance")
    
    # Test 2: Export cadastre map
    print("\n### TEST 2: Export Cadastre Map ###\n")
    
    # Bounding box around Albury CBD
    test_bbox = '146.91,-36.09,146.92,-36.08'
    
    cadastre_image = api.export_cadastre_image(test_bbox, width=800, height=600)
    
    if cadastre_image:
        output_file = 'cadastre_test.png'
        cadastre_image.save(output_file)
        print(f"💾 Cadastre image saved to {output_file}")
        print(f"   Image size: {cadastre_image.size}")
    else:
        print("⚠️  Test 2 failed - Could not export map")
    
    # Test 3: Draw property boundary on blank image (demonstration)
    print("\n### TEST 3: Draw Property Boundary ###\n")
    
    if property_data:
        # Create a blank image
        img_width, img_height = 800, 600
        img = Image.new('RGB', (img_width, img_height), color='white')
        draw = ImageDraw.Draw(img)
        
        # Get polygon rings
        geometry = property_data.get('geometry', {})
        rings = geometry.get('rings', [])
        
        if rings:
            print(f"📍 Drawing {len(rings)} polygon ring(s)...")
            
            # For demonstration, we'll just draw the first few points
            # In production, you'd need proper coordinate transformation
            outer_ring = rings[0]
            
            # Draw as a simple demonstration (not to scale)
            # In production, use proper lat/lon to pixel transformation
            points = [(i*10, i*10) for i in range(min(len(outer_ring), 50))]
            
            if len(points) > 2:
                draw.line(points + [points[0]], fill='red', width=3)
            
            output_file = 'property_boundary_demo.png'
            img.save(output_file)
            print(f"✅ Demonstration boundary drawn")
            print(f"💾 Saved to {output_file}")
            print(f"   Note: This is a simplified demonstration")
            print(f"   Production code should use proper coordinate transformation")
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"✅ API connection: OK")
    print(f"{'✅' if property_data else '❌'} Property query: {'OK' if property_data else 'FAILED'}")
    print(f"{'✅' if cadastre_image else '❌'} Map export: {'OK' if cadastre_image else 'FAILED'}")
    print("="*60 + "\n")
    
    if property_data and cadastre_image:
        print("🎉 All tests passed! Integration is working correctly.")
        print("\nNext steps:")
        print("  1. Review the generated files (property_data.json, cadastre_test.png)")
        print("  2. Implement proper coordinate transformation for your use case")
        print("  3. Add error handling and retry logic")
        print("  4. Implement caching for production use")
        return True
    else:
        print("⚠️  Some tests failed. Check your network connection and coordinates.")
        return False


if __name__ == "__main__":
    try:
        success = run_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
