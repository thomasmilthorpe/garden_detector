#!/usr/bin/env python3
"""
Compile all garden analysis CSV files into a master CSV and generate analysis report.

This script:
1. Iterates through all CSV files in garden_analysis_streets subfolders
2. Combines them into a master CSV in master_analysis folder
3. Generates a text analysis report with statistics
"""

import os
import csv
from pathlib import Path
from datetime import datetime


def find_all_csv_files(base_folder: str) -> list:
    """
    Find all CSV files in the garden_analysis_streets subfolders.

    Args:
        base_folder: Path to garden_analysis_streets folder

    Returns:
        List of paths to CSV files
    """
    csv_files = []

    # Iterate through each street subfolder
    for street_folder in os.listdir(base_folder):
        street_path = os.path.join(base_folder, street_folder)

        # Skip if not a directory
        if not os.path.isdir(street_path):
            continue

        # Find CSV files in this street folder
        for file in os.listdir(street_path):
            if file.endswith('.csv'):
                csv_path = os.path.join(street_path, file)
                csv_files.append(csv_path)

    return csv_files


def compile_master_csv(csv_files: list, output_path: str) -> list:
    """
    Combine all CSV files into a single master CSV.

    Args:
        csv_files: List of CSV file paths to combine
        output_path: Path to output master CSV file

    Returns:
        List of all row dictionaries from combined CSV
    """
    all_rows = []
    fieldnames = ['address', 'garden_likelihood', 'reasoning']

    # Read all CSV files and collect rows
    for csv_file in csv_files:
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Only extract the fields we need to avoid field mismatch errors
                    clean_row = {
                        'address': row.get('address', ''),
                        'garden_likelihood': row.get('garden_likelihood', ''),
                        'reasoning': row.get('reasoning', '')
                    }
                    all_rows.append(clean_row)
        except Exception as e:
            print(f"Warning: Error reading {csv_file}: {e}")

    # Write master CSV
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    return all_rows


def generate_analysis_report(rows: list, output_path: str):
    """
    Generate analysis text report with statistics.

    Args:
        rows: List of row dictionaries from CSV
        output_path: Path to output text file
    """
    # Count addresses by likelihood
    total_analyzed = 0
    low_count = 0
    medium_count = 0
    high_count = 0
    empty_count = 0

    for row in rows:
        likelihood = row.get('garden_likelihood', '').strip().lower()

        if likelihood in ['low', 'medium', 'high']:
            total_analyzed += 1

            if likelihood == 'low':
                low_count += 1
            elif likelihood == 'medium':
                medium_count += 1
            elif likelihood == 'high':
                high_count += 1
        else:
            empty_count += 1

    # Calculate statistics
    medium_or_high_count = medium_count + high_count

    # Calculate proportions
    medium_or_high_proportion = (medium_or_high_count / total_analyzed * 100) if total_analyzed > 0 else 0
    high_proportion = (high_count / total_analyzed * 100) if total_analyzed > 0 else 0

    # Generate report
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    report = f"""Garden Analysis Report
{'=' * 60}
Generated: {timestamp}

SUMMARY
{'=' * 60}

Total addresses in dataset: {len(rows)}
Addresses not yet analyzed: {empty_count}

a) Addresses with completed analysis: {total_analyzed}
   (Analysis marked as low, medium, or high likelihood)

   Breakdown:
   - Low likelihood:    {low_count:4d} ({low_count/total_analyzed*100:5.1f}%)
   - Medium likelihood: {medium_count:4d} ({medium_count/total_analyzed*100:5.1f}%)
   - High likelihood:   {high_count:4d} ({high_count/total_analyzed*100:5.1f}%)

b) Addresses with MEDIUM or HIGH likelihood: {medium_or_high_count}
   Proportion: {medium_or_high_proportion:.1f}% of analyzed addresses
   ({medium_or_high_count} out of {total_analyzed} addresses)

c) Addresses with HIGH likelihood only: {high_count}
   Proportion: {high_proportion:.1f}% of analyzed addresses
   ({high_count} out of {total_analyzed} addresses)

{'=' * 60}
End of Report
"""

    # Write report to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)

    return report


def main():
    """Main function to compile CSV and generate analysis."""
    print("=" * 60)
    print("Garden Analysis Compiler")
    print("=" * 60)

    # Define paths
    base_folder = os.path.join(os.getcwd(), 'garden_analysis_streets')
    master_folder = os.path.join(os.getcwd(), 'master_analysis')
    master_csv_path = os.path.join(master_folder, 'master_garden_analysis.csv')
    analysis_report_path = os.path.join(master_folder, 'analysis_report.txt')

    # Check if source folder exists
    if not os.path.exists(base_folder):
        print(f"\nError: Folder not found: {base_folder}")
        return

    # Create master_analysis folder if it doesn't exist
    print(f"\nCreating master_analysis folder...")
    os.makedirs(master_folder, exist_ok=True)
    print(f"✓ Folder ready: {master_folder}")

    # Find all CSV files
    print(f"\nSearching for CSV files in {base_folder}...")
    csv_files = find_all_csv_files(base_folder)

    if not csv_files:
        print("No CSV files found!")
        return

    print(f"✓ Found {len(csv_files)} CSV file(s)")
    for csv_file in csv_files:
        print(f"  - {os.path.basename(csv_file)}")

    # Compile master CSV
    print(f"\nCompiling master CSV...")
    all_rows = compile_master_csv(csv_files, master_csv_path)
    print(f"✓ Master CSV created: {master_csv_path}")
    print(f"  Total rows: {len(all_rows)}")

    # Generate analysis report
    print(f"\nGenerating analysis report...")
    report = generate_analysis_report(all_rows, analysis_report_path)
    print(f"✓ Analysis report created: {analysis_report_path}")

    # Display report
    print("\n" + report)

    print("=" * 60)
    print("Processing complete!")
    print("=" * 60)
    print(f"\nOutput files:")
    print(f"  - Master CSV: {master_csv_path}")
    print(f"  - Analysis Report: {analysis_report_path}")


if __name__ == "__main__":
    main()
