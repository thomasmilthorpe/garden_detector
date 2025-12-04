# Address Range Feature

## Overview

Added two modes for determining which house numbers to search on a street:

### 1. Auto Mode (Default)
- Automatically detects the address range
- Finds the nearest house number to the street's geocenter
- Searches ±200 numbers around that center point
- Falls back to common ranges (1-200, 100-300, 200-400) if auto-detection fails

### 2. Manual Mode
- User specifies minimum and maximum house numbers
- Searches only within that specific range
- Useful when you know the exact address range
- Saves time and API calls by focusing on relevant addresses

## Changes Made

### Modified Files:

1. **`geocoding.py`**
   - Updated `enumerate_street_addresses()` function
   - Added `min_number` and `max_number` optional parameters
   - Added logic to use manual range when provided, otherwise use auto mode

2. **`garden_detector.py`**
   - Updated `GardenDetector.geocode_street()` to accept range parameters
   - Updated `process_street()` to pass range parameters through
   - Updated `process_single_street()` to support range parameters
   - Modified `main()` to prompt user for range mode selection
   - Added variables initialization for all code paths

3. **`README.md`**
   - Updated Interactive Mode section to document the new feature
   - Updated How It Works section to explain both modes
   - Added comprehensive examples for both Auto and Manual modes
   - Added use cases for when to use Manual mode

## Usage

### Interactive Mode

When running the application interactively:

```bash
python garden_detector.py
```

You'll now see an additional prompt when analyzing a specific street:

```
Choose address range mode:
  1. Auto (automatically detect range)
  2. Manual (specify min/max numbers)
Enter choice (1 or 2):
```

**Option 1 (Auto)**: No additional input needed - the app automatically determines the range

**Option 2 (Manual)**: You'll be prompted for:
- Minimum house number (e.g., 100)
- Maximum house number (e.g., 200)

## Benefits

- **More Control**: Target specific address ranges
- **Efficiency**: Reduce API calls by limiting search scope
- **Flexibility**: Choose between automatic convenience and manual precision
- **Better Results**: Focus on relevant addresses when you know the street layout

## Examples

### Auto Mode
```
Choose address range mode: 1
# Automatically searches around the street center
```

### Manual Mode
```
Choose address range mode: 2
Enter minimum house number: 100
Enter maximum house number: 150
# Searches only addresses 100-150
```

## Technical Details

The manual range feature:
- Validates input and provides sensible defaults (1 for min, 200 for max)
- Still performs ROOFTOP-level verification for each address
- Maintains all existing safety checks and street name validation
- Works seamlessly with the existing file organization system
