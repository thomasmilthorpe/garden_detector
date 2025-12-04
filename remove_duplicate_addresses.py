"""
Standalone script to remove duplicate addresses from street analysis CSV files.

This script:
1. Scans all street folders in garden_analysis_streets/
2. For each CSV file, identifies duplicate addresses based on house number
3. When duplicates are found, keeps the entry with garden_likelihood value
4. If both have values, keeps the first occurrence
5. Updates the CSV file with duplicates removed
"""

import os
import csv
import re
from typing import Dict, List, Tuple


def extract_house_number(address: str) -> str:
    """
    Extract the house number from an address string.
    
    Args:
        address: Full address string
        
    Returns:
        House number as string, or empty string if no number found
        
    Examples:
        "232 Wirraway St, East Albury" -> "232"
        "114 Wirraway Street, Albury" -> "114"
        "Wirraway St, East Albury" -> "" (no number)
    """
    # Look for number at the start of the address
    match = re.match(r'^(\d+)\s', address.strip())
    if match:
        return match.group(1)
    return ""


def load_csv_rows(csv_path: str) -> Tuple[List[str], List[Dict]]:
    """
    Load CSV file and return headers and rows.
    
    Args:
        csv_path: Path to CSV file
        
    Returns:
        Tuple of (headers list, rows list)
    """
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        rows = list(reader)
    return headers, rows


def has_garden_likelihood(row: Dict) -> bool:
    """
    Check if a row has a garden_likelihood value.
    
    Args:
        row: Dictionary representing a CSV row
        
    Returns:
        True if garden_likelihood field exists and is not empty
    """
    return 'garden_likelihood' in row and row['garden_likelihood'].strip() != ''


def remove_duplicates(rows: List[Dict]) -> Tuple[List[Dict], int]:
    """
    Remove duplicate addresses based on house number.
    
    Strategy:
    - Group rows by house number
    - For duplicates, prefer rows with garden_likelihood value
    - If multiple rows have values, keep the first one
    - If no rows have values, keep the first one
    
    Args:
        rows: List of row dictionaries
        
    Returns:
        Tuple of (deduplicated rows, number of duplicates removed)
    """
    # Group rows by house number
    house_number_groups: Dict[str, List[Dict]] = {}
    no_number_rows = []
    
    for row in rows:
        address = row.get('address', '')
        house_number = extract_house_number(address)
        
        if house_number:
            if house_number not in house_number_groups:
                house_number_groups[house_number] = []
            house_number_groups[house_number].append(row)
        else:
            # Keep rows without house numbers (like "Wirraway St" without number)
            no_number_rows.append(row)
    
    # Process each group and select the best row
    deduplicated = []
    duplicates_removed = 0
    
    for house_number, group in sorted(house_number_groups.items(), key=lambda x: int(x[0])):
        if len(group) == 1:
            # No duplicates for this house number
            deduplicated.append(group[0])
        else:
            # Duplicates found - select the best one
            duplicates_removed += len(group) - 1
            
            # Separate rows with and without garden_likelihood
            with_likelihood = [row for row in group if has_garden_likelihood(row)]
            without_likelihood = [row for row in group if not has_garden_likelihood(row)]
            
            if with_likelihood:
                # Keep the first row with garden_likelihood
                selected_row = with_likelihood[0]
                print(f"    Duplicate {house_number}: Kept entry with garden_likelihood, removed {len(group)-1} duplicate(s)")
            else:
                # No rows have garden_likelihood, keep the first one
                selected_row = group[0]
                print(f"    Duplicate {house_number}: No garden_likelihood values, kept first entry, removed {len(group)-1} duplicate(s)")
            
            deduplicated.append(selected_row)
    
    # Add rows without house numbers at the beginning
    result = no_number_rows + deduplicated
    
    return result, duplicates_removed


def save_csv_rows(csv_path: str, headers: List[str], rows: List[Dict]):
    """
    Save rows to CSV file.
    
    Args:
        csv_path: Path to CSV file
        headers: List of column headers
        rows: List of row dictionaries
    """
    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def process_csv_file(csv_path: str) -> int:
    """
    Process a single CSV file to remove duplicates.
    
    Args:
        csv_path: Path to CSV file
        
    Returns:
        Number of duplicates removed
    """
    # Load CSV
    headers, rows = load_csv_rows(csv_path)
    
    if not rows:
        print(f"  No rows found, skipping")
        return 0
    
    original_count = len(rows)
    
    # Remove duplicates
    deduplicated_rows, duplicates_removed = remove_duplicates(rows)
    
    if duplicates_removed > 0:
        # Save updated CSV
        save_csv_rows(csv_path, headers, deduplicated_rows)
        print(f"  Removed {duplicates_removed} duplicate(s): {original_count} -> {len(deduplicated_rows)} addresses")
    else:
        print(f"  No duplicates found ({original_count} unique addresses)")
    
    return duplicates_removed


def process_all_streets(base_folder: str):
    """
    Process all street CSV files in the garden_analysis_streets folder.
    
    Args:
        base_folder: Path to garden_analysis_streets folder
    """
    if not os.path.exists(base_folder):
        print(f"Error: Folder not found: {base_folder}")
        return
    
    total_duplicates = 0
    total_files = 0
    
    # Get all street folders
    street_folders = [f for f in os.listdir(base_folder) 
                     if os.path.isdir(os.path.join(base_folder, f))]
    
    if not street_folders:
        print("No street folders found")
        return
    
    print(f"Found {len(street_folders)} street folder(s)\n")
    
    # Process each street folder
    for street_folder in sorted(street_folders):
        folder_path = os.path.join(base_folder, street_folder)
        
        # Find CSV files in this folder
        csv_files = [f for f in os.listdir(folder_path) if f.endswith('.csv')]
        
        for csv_file in csv_files:
            csv_path = os.path.join(folder_path, csv_file)
            print(f"Processing: {street_folder}/{csv_file}")
            
            try:
                duplicates_removed = process_csv_file(csv_path)
                total_duplicates += duplicates_removed
                total_files += 1
            except Exception as e:
                print(f"  Error processing file: {e}")
            
            print()
    
    # Print summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Files processed: {total_files}")
    print(f"Total duplicates removed: {total_duplicates}")


def main():
    """Main entry point."""
    print("=" * 60)
    print("Remove Duplicate Addresses from Street Analysis CSVs")
    print("=" * 60)
    print()
    
    # Base folder containing street analysis
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_folder = os.path.join(script_dir, 'garden_analysis_streets')
    
    process_all_streets(base_folder)


if __name__ == "__main__":
    main()
