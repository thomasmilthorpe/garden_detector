#!/usr/bin/env python3
"""
Garden Detection Application
Analyzes Google Maps satellite imagery to detect vegetable gardens in suburban addresses.

Refactored into modular components for easier maintenance and use.
"""

import sys
import time
import csv
import os
from typing import List, Dict

# Import configuration and validation
from config import validate_api_keys, DEFAULT_MAX_ADDRESSES, DEFAULT_MAX_STREETS

# Import modular components
from geocoding import geocode_street, enumerate_street_addresses
from cadastre import get_nsw_property_boundary
from image_processing import get_satellite_image, save_satellite_image, image_exists
from ai_analysis import analyze_garden_likelihood
from file_manager import (get_street_folder, load_existing_addresses, count_existing_addresses, 
                          save_to_csv, ensure_csv_exists, add_address_to_csv, 
                          update_address_analysis, is_analysis_complete, get_csv_path)
from street_finder import get_streets_in_suburb


class GardenDetector:
    """Main class for detecting gardens in suburban addresses."""
    
    def __init__(self):
        self.results = []
    
    def geocode_street(self, street_name: str, suburb: str, num_addresses: int = 20,
                      min_number: int = None, max_number: int = None) -> List[Dict]:
        """
        Find addresses along a street using Google Maps Geocoding API.
        Checks for existing addresses first and only fetches new ones if needed.
        
        Args:
            street_name: Name of the street
            suburb: Suburb or city name
            num_addresses: Total number of addresses desired
            min_number: Minimum house number (manual mode)
            max_number: Maximum house number (manual mode)
            
        Returns:
            List of address dictionaries with location data
        """
        print(f"\nSearching for addresses on {street_name}, {suburb}...")
        
        # Check how many addresses we already have
        existing_count = count_existing_addresses(street_name, suburb)
        existing_addresses = load_existing_addresses(street_name, suburb) if existing_count > 0 else []
        
        if existing_count >= num_addresses:
            print(f"✓ Analysis already completed - {existing_count} addresses found (requested: {num_addresses})")
            print(f"  Skipping address collection for this street.")
            return []
        elif existing_count > 0:
            print(f"Found {existing_count} existing addresses, need {num_addresses - existing_count} more")
        
        # Search for the street
        street_data = geocode_street(street_name, suburb)
        
        if not street_data:
            print(f"Could not find street: {street_name}, {suburb}")
            return []
        
        # Enumerate addresses along the street
        # Request more than needed to account for duplicates
        addresses_needed = num_addresses - existing_count
        all_addresses = enumerate_street_addresses(
            street_name, suburb, street_data['location'],
            num_addresses=addresses_needed * 2,  # Request extra to filter duplicates
            min_number=min_number, max_number=max_number
        )
        
        # Filter out addresses that already exist
        if existing_addresses:
            existing_set = set(existing_addresses)
            new_addresses = [addr for addr in all_addresses if addr['address'] not in existing_set]
            print(f"Filtered out {len(all_addresses) - len(new_addresses)} duplicate addresses")
        else:
            new_addresses = all_addresses
        
        # Return only the number we need
        return new_addresses[:addresses_needed]
    
    def analyze_addresses(self, addresses: List[Dict], street_name: str, suburb: str) -> List[Dict]:
        """
        Analyze a list of addresses for garden likelihood.
        Processes each address incrementally, updating CSV after each one.
        
        Args:
            addresses: List of address dictionaries with lat/lng
            street_name: Name of the street
            suburb: Suburb name
            
        Returns:
            List of results with addresses and garden likelihood
        """
        results = []
        
        if not addresses:
            print("No addresses to analyze.")
            return results
        
        # Ensure CSV exists with headers
        ensure_csv_exists(street_name, suburb)
        street_folder = get_street_folder(street_name, suburb)
        
        print(f"\nAnalyzing {len(addresses)} addresses on {street_name}...")
        
        for i, addr_info in enumerate(addresses, 1):
            address = addr_info['address']
            lat = addr_info['lat']
            lng = addr_info['lng']
            
            print(f"\n[{i}/{len(addresses)}] Processing: {address}")
            
            # Step 1: Add address to CSV if it doesn't exist
            add_address_to_csv(street_name, suburb, address)
            
            # Step 2: Check if analysis is already complete for this address
            if is_analysis_complete(street_name, suburb, address):
                print(f"  ✓ Analysis already complete for this address, skipping...")
                continue
            
            # Step 3: Check if image already exists
            if image_exists(street_folder, address):
                print(f"  ✓ Image already exists, skipping download...")
                # Load the existing image
                from PIL import Image
                from io import BytesIO
                image_path = os.path.join(street_folder, f"{address.split()[0]}.jpg")
                with open(image_path, 'rb') as f:
                    annotated_image = f.read()
            else:
                # Step 4: Get property boundary to find centroid
                print(f"  Fetching property boundary to determine centroid...")
                boundary_rings = get_nsw_property_boundary(lat, lng)
                
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
                image_data = get_satellite_image(centroid_lat, centroid_lng)
                
                if not image_data:
                    print(f"  Skipping - could not retrieve image")
                    update_address_analysis(street_name, suburb, address, 'unknown', 
                                          'Could not retrieve satellite image')
                    continue
                
                # Save satellite image with property boundary
                print(f"  Downloading and annotating image...")
                filepath, annotated_image = save_satellite_image(
                    image_data, street_folder, address, lat, lng, centroid_lat, centroid_lng
                )
            
            # Step 5: Analyze for garden using annotated image
            print(f"  Analyzing image with AI...")
            analysis = analyze_garden_likelihood(annotated_image, address)
            
            print(f"  Garden likelihood: {analysis['likelihood'].upper()}")
            print(f"  Reasoning: {analysis['reasoning'][:100]}...")  # Print first 100 chars
            
            # Step 6: Update CSV immediately with analysis results
            update_address_analysis(street_name, suburb, address, 
                                   analysis['likelihood'], analysis['reasoning'])
            print(f"  ✓ Results saved to CSV")
            
            results.append({
                'address': address,
                'garden_likelihood': analysis['likelihood'],
                'reasoning': analysis['reasoning']
            })
            
            # Rate limiting to avoid API throttling
            time.sleep(0.1)
        
        return results
    
    def process_street(self, street_name: str, suburb: str, max_addresses: int = DEFAULT_MAX_ADDRESSES,
                      min_number: int = None, max_number: int = None) -> List[Dict]:
        """
        Main processing function: find addresses and analyze for gardens.
        
        Args:
            street_name: Name of the street
            suburb: Suburb or city
            max_addresses: Maximum number of addresses to process
            min_number: Minimum house number (manual mode)
            max_number: Maximum house number (manual mode)
            save_results: Whether to save results to CSV after processing (deprecated - now saves incrementally)
            
        Returns:
            List of results with addresses and garden likelihood
        """
        # Ensure CSV exists with proper headers
        ensure_csv_exists(street_name, suburb)
        
        # Get addresses (checks existing and only fetches new ones if needed)
        addresses = self.geocode_street(street_name, suburb, max_addresses, min_number, max_number)
        
        if not addresses:
            # Either already completed or no addresses found
            existing_count = count_existing_addresses(street_name, suburb)
            if existing_count >= max_addresses:
                print(f"Street analysis already complete with {existing_count} addresses.")
            else:
                print("No new addresses found.")
            return []
        
        # Analyze addresses (saves incrementally to CSV)
        results = self.analyze_addresses(addresses, street_name, suburb)
        
        # Print final summary
        if results:
            csv_path = get_csv_path(street_name, suburb)
            print(f"\n✓ Street processing complete: {csv_path}")
            print(f"  Processed {len(results)} new addresses")
        
        return results
    
    def save_results(self, street_name: str, suburb: str):
        """
        Save results to CSV file in street folder.
        
        Args:
            street_name: Name of the street
            suburb: Suburb name
        """
        street_folder = get_street_folder(street_name, suburb)
        output_filename = f"garden_analysis_{street_name.replace(' ', '_')}_{suburb.replace(' ', '_')}.csv"
        save_to_csv(self.results, output_filename, street_folder)


def process_single_street(detector: GardenDetector, street_name: str, suburb: str, 
                         max_addresses: int, min_number: int = None, max_number: int = None):
    """Process a single street and save results."""
    print(f"\n{'='*60}")
    print(f"Processing: {street_name}, {suburb}")
    print(f"{'='*60}")
    
    # Process street (results are automatically saved)
    detector.process_street(street_name, suburb, max_addresses, min_number, max_number)


def process_multiple_streets(detector: GardenDetector, suburb: str, max_addresses: int, max_streets: int):
    """Process multiple streets in a suburb, saving results incrementally after each address."""
    streets = get_streets_in_suburb(suburb, max_streets)
    
    if not streets:
        print("No streets found.")
        sys.exit(1)
    
    print(f"\nWill analyze {len(streets)} streets:")
    for i, street in enumerate(streets, 1):
        print(f"  {i}. {street['name']}")
    
    # Process each street
    for i, street_info in enumerate(streets, 1):
        print(f"\n{'='*60}")
        print(f"Processing street {i}/{len(streets)}: {street_info['name']}")
        print(f"{'='*60}")
        
        # Ensure CSV exists
        ensure_csv_exists(street_info['name'], suburb)
        
        # Check existing progress for this street
        existing_count = count_existing_addresses(street_info['name'], suburb)
        
        if existing_count >= max_addresses:
            print(f"✓ Analysis already completed - {existing_count} addresses found (requested: {max_addresses})")
            print(f"  Skipping this street.")
            continue
        elif existing_count > 0:
            print(f"Found {existing_count} existing addresses, need {max_addresses - existing_count} more")
        
        # Process street (handles incremental updates internally)
        detector.process_street(street_info['name'], suburb, max_addresses)
    
    print(f"\n✓ Completed processing {len(streets)} streets in {suburb}")


def main():
    """Main entry point for the application."""
    print("=" * 60)
    print("Garden Detection Application")
    print("=" * 60)
    
    # Validate API keys
    validate_api_keys()
    
    # Create detector
    detector = GardenDetector()
    
    # Get user input
    if len(sys.argv) >= 2:
        suburb = sys.argv[1]
        max_addresses = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_MAX_ADDRESSES
        max_streets = int(sys.argv[3]) if len(sys.argv) > 3 else DEFAULT_MAX_STREETS
        street_name = None
        min_number = None
        max_number = None
    else:
        mode = input("\nChoose mode:\n  1. Analyze specific street\n  2. Analyze multiple streets in suburb\nEnter choice (1 or 2): ").strip()
        
        if mode == '1':
            # Single street mode
            street_name = input("\nEnter street name: ").strip()
            suburb = input("Enter suburb/city: ").strip()
            
            # Ask for range mode
            range_mode = input("\nChoose address range mode:\n  1. Auto (automatically detect range)\n  2. Manual (specify min/max numbers)\nEnter choice (1 or 2): ").strip()
            
            if range_mode == '2':
                # Manual range mode
                min_input = input("Enter minimum house number: ").strip()
                max_input_range = input("Enter maximum house number: ").strip()
                min_number = int(min_input) if min_input else 1
                max_number = int(max_input_range) if max_input_range else 200
            else:
                # Auto mode
                min_number = None
                max_number = None
            
            max_input = input(f"Enter max number of addresses to analyze (default {DEFAULT_MAX_ADDRESSES}): ").strip()
            max_addresses = int(max_input) if max_input else DEFAULT_MAX_ADDRESSES
            max_streets = 1
        else:
            # Multiple streets mode
            suburb = input("\nEnter suburb/city: ").strip()
            max_input = input(f"Enter max number of addresses per street (default {DEFAULT_MAX_ADDRESSES}): ").strip()
            max_addresses = int(max_input) if max_input else DEFAULT_MAX_ADDRESSES
            streets_input = input(f"Enter number of streets to analyze (default {DEFAULT_MAX_STREETS}): ").strip()
            max_streets = int(streets_input) if streets_input else DEFAULT_MAX_STREETS
            street_name = None
            min_number = None
            max_number = None
    
    if not suburb:
        print("Error: Suburb is required.")
        sys.exit(1)
    
    try:
        if street_name:
            # Single street mode
            process_single_street(detector, street_name, suburb, max_addresses, min_number, max_number)
        else:
            # Multiple streets mode
            process_multiple_streets(detector, suburb, max_addresses, max_streets)
        
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
