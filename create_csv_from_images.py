#!/usr/bin/env python3
"""
Create CSV files from existing image folders.
Scans garden_analysis_streets folders and creates CSV files with proper headers
based on the image files present in each folder.
"""

import os
import csv
import re
from pathlib import Path


def extract_house_number(filename: str) -> str:
    """
    Extract house number from image filename.
    
    Args:
        filename: Image filename (e.g., "123.jpg")
        
    Returns:
        House number as string, or None if not found
    """
    # Remove extension
    name = os.path.splitext(filename)[0]
    
    # Try to extract number
    match = re.match(r'^(\d+)', name)
    if match:
        return match.group(1)
    return None


def parse_folder_name(folder_name: str) -> tuple:
    """
    Parse street folder name to extract street name and suburb.
    
    Args:
        folder_name: Folder name (e.g., "North_Street_East_Albury")
        
    Returns:
        Tuple of (street_name, suburb) with underscores replaced by spaces
    """
    # The folder name format is: StreetName_Suburb
    # We need to split on the last underscore to separate suburb
    parts = folder_name.rsplit('_', 1)
    
    if len(parts) == 2:
        street = parts[0].replace('_', ' ')
        suburb = parts[1].replace('_', ' ')
        return street, suburb
    else:
        # If we can't parse it, just use the folder name
        return folder_name.replace('_', ' '), "Unknown"


def create_csv_for_street(street_folder_path: str):
    """
    Create a CSV file for a street folder based on image files present.
    
    Args:
        street_folder_path: Path to the street folder
    """
    folder_name = os.path.basename(street_folder_path)
    street_name, suburb = parse_folder_name(folder_name)
    
    # Expected CSV filename
    csv_filename = f"garden_analysis_{folder_name}.csv"
    csv_path = os.path.join(street_folder_path, csv_filename)
    
    # Check if CSV already exists
    if os.path.exists(csv_path):
        print(f"  ✓ CSV already exists: {csv_filename}")
        return
    
    # Find all image files in the folder
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp'}
    image_files = []
    
    for file in os.listdir(street_folder_path):
        file_path = os.path.join(street_folder_path, file)
        if os.path.isfile(file_path):
            ext = os.path.splitext(file)[1].lower()
            if ext in image_extensions:
                image_files.append(file)
    
    if not image_files:
        print(f"  ℹ No image files found in {folder_name}")
        return
    
    # Sort image files by house number
    image_files.sort(key=lambda x: int(extract_house_number(x)) if extract_house_number(x) else 0)
    
    # Create CSV with addresses based on house numbers
    addresses = []
    for img_file in image_files:
        house_number = extract_house_number(img_file)
        if house_number:
            # Construct address from house number, street name, and suburb
            address = f"{house_number} {street_name}, {suburb}"
            addresses.append({
                'address': address,
                'garden_likelihood': '',
                'reasoning': ''
            })
    
    if not addresses:
        print(f"  ℹ No valid house numbers found in image files for {folder_name}")
        return
    
    # Write CSV file
    try:
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['address', 'garden_likelihood', 'reasoning']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for addr_data in addresses:
                writer.writerow(addr_data)
        
        print(f"  ✓ Created CSV: {csv_filename} ({len(addresses)} addresses)")
    
    except Exception as e:
        print(f"  ✗ Error creating CSV for {folder_name}: {e}")


def main():
    """Main function to process all street folders."""
    print("=" * 60)
    print("Create CSV Files from Image Folders")
    print("=" * 60)
    
    # Get the garden_analysis_streets folder
    base_folder = os.path.join(os.getcwd(), 'garden_analysis_streets')
    
    if not os.path.exists(base_folder):
        print(f"\nError: Folder not found: {base_folder}")
        print("Make sure you're running this script from the project root directory.")
        return
    
    # Get all subdirectories (street folders)
    street_folders = []
    for item in os.listdir(base_folder):
        item_path = os.path.join(base_folder, item)
        if os.path.isdir(item_path):
            street_folders.append(item_path)
    
    if not street_folders:
        print(f"\nNo street folders found in {base_folder}")
        return
    
    print(f"\nFound {len(street_folders)} street folders")
    print("-" * 60)
    
    # Process each street folder
    for street_folder in sorted(street_folders):
        folder_name = os.path.basename(street_folder)
        print(f"\nProcessing: {folder_name}")
        create_csv_for_street(street_folder)
    
    print("\n" + "=" * 60)
    print("Processing complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
