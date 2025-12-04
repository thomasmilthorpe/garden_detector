"""
File management module for Garden Detector application.
Handles file and folder operations for organizing analysis results.
"""

import os
import csv
import time
import requests
from typing import List, Dict, Optional
from config import GOOGLE_MAPS_API_KEY, GOOGLE_MAPS_BASE_URL


def get_street_folder(street_name: str, suburb: str) -> str:
    """
    Get the folder path for a street's analysis data.
    
    Args:
        street_name: Name of the street
        suburb: Suburb name
        
    Returns:
        Folder path string
    """
    safe_street = street_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
    safe_suburb = suburb.replace(' ', '_').replace('/', '_').replace('\\', '_')
    folder_name = f"{safe_street}_{safe_suburb}"
    return os.path.join(os.getcwd(), 'garden_analysis_streets', folder_name)


def load_existing_addresses(street_name: str, suburb: str) -> Optional[List[str]]:
    """
    Load previously analyzed addresses from CSV if available.
    Returns just the address strings (not full analysis results).
    
    Args:
        street_name: Name of the street
        suburb: Suburb name
        
    Returns:
        List of address strings, or None if not found
    """
    street_folder = get_street_folder(street_name, suburb)
    csv_path = os.path.join(
        street_folder, 
        f"garden_analysis_{street_name.replace(' ', '_')}_{suburb.replace(' ', '_')}.csv"
    )
    
    if not os.path.exists(csv_path):
        return None
    
    print(f"Found existing analysis at {csv_path}")
    
    addresses = []
    try:
        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                addresses.append(row['address'])
        
        print(f"Loaded {len(addresses)} addresses from previous analysis")
        return addresses if addresses else None
        
    except Exception as e:
        print(f"Error loading existing addresses: {e}")
        return None


def get_csv_path(street_name: str, suburb: str) -> str:
    """
    Get the CSV file path for a street.
    
    Args:
        street_name: Name of the street
        suburb: Suburb name
        
    Returns:
        Full path to CSV file
    """
    street_folder = get_street_folder(street_name, suburb)
    csv_filename = f"garden_analysis_{street_name.replace(' ', '_')}_{suburb.replace(' ', '_')}.csv"
    return os.path.join(street_folder, csv_filename)


def ensure_csv_exists(street_name: str, suburb: str):
    """
    Ensure CSV file exists with proper headers.
    Creates it if it doesn't exist.
    
    Args:
        street_name: Name of the street
        suburb: Suburb name
    """
    street_folder = get_street_folder(street_name, suburb)
    os.makedirs(street_folder, exist_ok=True)
    
    csv_path = get_csv_path(street_name, suburb)
    
    if not os.path.exists(csv_path):
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['address', 'garden_likelihood', 'reasoning']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()


def load_csv_as_dict(street_name: str, suburb: str) -> Dict[str, Dict]:
    """
    Load CSV as a dictionary keyed by address.
    
    Args:
        street_name: Name of the street
        suburb: Suburb name
        
    Returns:
        Dictionary with addresses as keys and row data as values
    """
    csv_path = get_csv_path(street_name, suburb)
    
    if not os.path.exists(csv_path):
        return {}
    
    address_dict = {}
    try:
        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                address_dict[row['address']] = row
        return address_dict
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return {}


def add_address_to_csv(street_name: str, suburb: str, address: str):
    """
    Add an address to CSV with empty analysis fields if it doesn't exist.
    
    Args:
        street_name: Name of the street
        suburb: Suburb name
        address: Address to add
    """
    ensure_csv_exists(street_name, suburb)
    csv_path = get_csv_path(street_name, suburb)
    
    # Load existing addresses
    existing_data = load_csv_as_dict(street_name, suburb)
    
    # Check if address already exists
    if address in existing_data:
        return  # Already exists, don't add again
    
    # Add new address with empty fields
    existing_data[address] = {
        'address': address,
        'garden_likelihood': '',
        'reasoning': ''
    }
    
    # Write all data back to CSV
    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['address', 'garden_likelihood', 'reasoning']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for addr_data in existing_data.values():
            writer.writerow(addr_data)


def update_address_analysis(street_name: str, suburb: str, address: str, 
                            garden_likelihood: str, reasoning: str):
    """
    Update the analysis for a specific address in the CSV.
    
    Args:
        street_name: Name of the street
        suburb: Suburb name
        address: Address to update
        garden_likelihood: Garden likelihood value
        reasoning: Analysis reasoning
    """
    ensure_csv_exists(street_name, suburb)
    csv_path = get_csv_path(street_name, suburb)
    
    # Load existing data
    existing_data = load_csv_as_dict(street_name, suburb)
    
    # Update or add the address
    existing_data[address] = {
        'address': address,
        'garden_likelihood': garden_likelihood,
        'reasoning': reasoning
    }
    
    # Write all data back to CSV
    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['address', 'garden_likelihood', 'reasoning']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for addr_data in existing_data.values():
            writer.writerow(addr_data)


def is_analysis_complete(street_name: str, suburb: str, address: str) -> bool:
    """
    Check if analysis is complete for a specific address.
    
    Args:
        street_name: Name of the street
        suburb: Suburb name
        address: Address to check
        
    Returns:
        True if analysis is complete (has garden_likelihood value), False otherwise
    """
    existing_data = load_csv_as_dict(street_name, suburb)
    
    if address not in existing_data:
        return False
    
    # Analysis is complete if garden_likelihood is not empty
    return bool(existing_data[address].get('garden_likelihood', '').strip())


def count_existing_addresses(street_name: str, suburb: str) -> int:
    """
    Count how many addresses have already been analyzed for a street.
    
    Args:
        street_name: Name of the street
        suburb: Suburb name
        
    Returns:
        Number of addresses in existing CSV, or 0 if not found
    """
    existing = load_existing_addresses(street_name, suburb)
    return len(existing) if existing else 0


def save_to_csv(results: List[Dict], filename: str, street_folder: str = None):
    """
    Save results to a CSV file.
    
    Args:
        results: List of result dictionaries
        filename: Output filename
        street_folder: Specific folder path to save to (if None, saves to current directory)
    """
    if not results:
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
        for result in results:
            writer.writerow(result)
    
    print(f"\n✓ Results saved to: {filepath}")
    print(f"  Total addresses analyzed: {len(results)}")
    
    # Print summary statistics
    low = sum(1 for r in results if r['garden_likelihood'] == 'low')
    medium = sum(1 for r in results if r['garden_likelihood'] == 'medium')
    high = sum(1 for r in results if r['garden_likelihood'] == 'high')
    
    print(f"\n  Summary:")
    print(f"    Low likelihood:    {low}")
    print(f"    Medium likelihood: {medium}")
    print(f"    High likelihood:   {high}")
