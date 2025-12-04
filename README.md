# Garden Detection Application

An AI-powered Python application that analyzes Google Maps satellite imagery to detect the likelihood of vegetable gardens at suburban addresses.

## Features

- 🗺️ **Address Enumeration**: Automatically finds addresses along a specified street
- 🛰️ **Satellite Imagery**: Retrieves high-resolution satellite images from Google Maps
- 🤖 **AI Analysis**: Uses OpenAI's GPT-4 Vision to detect vegetable gardens
- 📊 **CSV Output**: Generates a CSV file with addresses and garden likelihood ratings

## Prerequisites

- Python 3.7 or higher
- Google Maps API key ([Get one here](https://console.cloud.google.com/))
  - Enable the following APIs:
    - Geocoding API
    - Maps Static API
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

## Installation

1. **Clone or download this repository**

2. **Create a virtual environment:**
   ```bash
   python -m venv .venv
   ```

3. **Activate the virtual environment:**
   ```bash
   # On Windows
   .venv\Scripts\activate
   
   # On macOS/Linux
   source .venv/bin/activate
   ```

4. **Install required packages:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Set up your API keys:**
   - Copy `.env.example` to `.env`:
     ```bash
     cp .env.example .env
     ```
   - Edit `.env` and add your API keys:
     ```
     GOOGLE_MAPS_API_KEY=your_actual_google_maps_api_key
     OPENAI_API_KEY=your_actual_openai_api_key
     ```

## Usage

### Interactive Mode

Run the script and follow the prompts:

```bash
python garden_detector.py
```

You'll be asked to enter:
- **Mode selection**: Analyze a specific street or multiple streets
- **Street name** (e.g., "Main Street") - if analyzing a specific street
- **Suburb/city** (e.g., "Springfield")
- **Address range mode** (for single street analysis):
  - **Auto mode**: Automatically detects the address range by finding the nearest house number
  - **Manual mode**: Specify minimum and maximum house numbers to search
- **Maximum number of addresses** to analyze (default: 20)

### Command Line Mode

You can also pass parameters directly:

```bash
python garden_detector.py "Main Street" "Springfield" 15
```

Arguments:
1. Street name
2. Suburb/city
3. Maximum addresses (optional, default: 20)

## Output

The application generates a CSV file named:
```
garden_analysis_[street_name]_[suburb].csv
```

### CSV Format

| address | garden_likelihood |
|---------|------------------|
| 123 Main Street, Springfield | high |
| 125 Main Street, Springfield | low |
| 127 Main Street, Springfield | medium |

### Garden Likelihood Ratings

- **low**: No clear evidence of a vegetable garden (mostly lawn, pavement, or natural vegetation)
- **medium**: Some signs that could be a garden (organized plantings, possible raised beds) but not definitive
- **high**: Clear evidence of a vegetable garden (visible rows, raised beds, organized cultivation)

## How It Works

1. **Address Discovery**: The app uses Google's Geocoding API to:
   - Locate the specified street
   - **Auto mode**: Automatically finds the nearest house number to the street center and searches ±200 numbers around it
   - **Manual mode**: Searches only within the specified range (min to max house numbers)
   - Verify which addresses actually exist (using ROOFTOP-level precision)

2. **Image Retrieval**: For each valid address:
   - Fetches a high-resolution satellite image (zoom level 20)
   - Uses Google Maps Static API

3. **AI Analysis**: Each image is analyzed by OpenAI's GPT-4 Vision model to:
   - Detect organized plant rows
   - Identify raised garden beds
   - Look for cultivated soil patterns
   - Distinguish gardens from regular lawns

4. **Results Export**: All findings are compiled into a CSV file with summary statistics

## API Costs

### Google Maps API
- Geocoding API: ~$5 per 1000 requests
- Static Maps API: ~$2 per 1000 requests

### OpenAI API
- GPT-4 Vision (gpt-4o-mini): ~$0.00015 per image

**Example cost** for analyzing 20 addresses: approximately $0.15-$0.20

## Limitations

- The app finds addresses by trying common house numbers; not all addresses may be discovered
- Accuracy depends on image quality and season (gardens may not be visible in winter)
- Dense tree cover can obscure gardens from satellite view
- API rate limits may slow down processing for large streets

## Troubleshooting

**"Error: Please set your Google Maps API key"**
- Make sure you've created a `.env` file (not `.env.example`)
- Verify your API key is correctly pasted

**"Error geocoding street"**
- Check that the street name and suburb are spelled correctly
- Try adding more specific location details (e.g., state/province)

**No addresses found**
- The street might be named differently in Google Maps
- Try varying the street name format (e.g., "Street" vs "St")

**Rate limit errors**
- The app includes delays to prevent rate limiting
- If you still hit limits, reduce the number of addresses processed

## Example

### Auto Mode (Default)

```bash
python garden_detector.py
```

```
====================================
Garden Detection Application
====================================

Choose mode:
  1. Analyze specific street
  2. Analyze multiple streets in suburb
Enter choice (1 or 2): 1

Enter street name: Elm Street
Enter suburb/city: Portland, OR

Choose address range mode:
  1. Auto (automatically detect range)
  2. Manual (specify min/max numbers)
Enter choice (1 or 2): 1

Enter max number of addresses to analyze (default 20): 10

Searching for addresses on Elm Street, Portland, OR...
Found street: Elm St, Portland, OR 97202, USA
Using auto mode to determine address range...
Finding nearest address to street geocentre...
  Found nearest address to geocentre: 125
Searching house numbers from 1 to 325...
Attempting to find valid addresses...
  Found: 123 SE Elm St, Portland, OR 97202, USA
  Found: 125 SE Elm St, Portland, OR 97202, USA
  ...

Analyzing 10 addresses for garden likelihood...

[1/10] Processing: 123 SE Elm St, Portland, OR 97202, USA
  Analyzing image with AI...
  Garden likelihood: HIGH

...

✓ Results saved to: garden_analysis_streets/Elm_Street_Portland_OR/garden_analysis_Elm_Street_Portland_OR.csv
  Total addresses analyzed: 10

  Summary:
    Low likelihood:    6
    Medium likelihood: 2
    High likelihood:   2
```

### Manual Mode

If you know the specific address range on a street:

```bash
python garden_detector.py
```

```
====================================
Garden Detection Application
====================================

Choose mode:
  1. Analyze specific street
  2. Analyze multiple streets in suburb
Enter choice (1 or 2): 1

Enter street name: Oak Avenue
Enter suburb/city: Springfield

Choose address range mode:
  1. Auto (automatically detect range)
  2. Manual (specify min/max numbers)
Enter choice (1 or 2): 2

Enter minimum house number: 100
Enter maximum house number: 150
Enter max number of addresses to analyze (default 20): 20

Searching for addresses on Oak Avenue, Springfield...
Found street: Oak Ave, Springfield, MA 01109, USA
Using manual range: 100 to 150
Attempting to find valid addresses...
  Found: 100 Oak Ave, Springfield, MA 01109, USA
  Found: 102 Oak Ave, Springfield, MA 01109, USA
  ...
```

This manual mode is useful when:
- You know the exact address range on a street
- You want to focus on a specific section of a long street
- Auto mode is finding addresses outside your area of interest

## License

This project is provided as-is for educational and research purposes.

## Contributing

Feel free to submit issues or pull requests to improve the application!
