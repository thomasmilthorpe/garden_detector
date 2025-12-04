# Garden Detector - Modular Structure

## Overview

The Garden Detector application has been refactored into a modular architecture for easier maintenance, testing, and extension. The monolithic `garden_detector.py` file has been split into focused modules, each handling a specific aspect of the application.

## Module Structure

### Core Modules

#### `config.py`
**Purpose:** Central configuration management
- API keys (Google Maps, OpenAI)
- Base URLs for all external services
- Application constants (zoom levels, image sizes, defaults)
- API key validation
- Rate limiting constants

#### `geocoding.py`
**Purpose:** Address and location discovery
- `find_nearest_house_number()` - Reverse geocode to find nearest address
- `enumerate_street_addresses()` - Discover all addresses along a street
- `geocode_street()` - Find street geocenter

#### `cadastre.py`
**Purpose:** NSW Cadastre property boundary integration
- `get_nsw_property_boundary()` - Fetch property boundaries from NSW Cadastre MapServer
- `draw_property_boundary_and_marker()` - Draw boundaries on satellite images

#### `image_processing.py`
**Purpose:** Satellite image retrieval and storage
- `get_satellite_image()` - Fetch satellite imagery from Google Maps
- `save_satellite_image()` - Save images with annotations to organized folders

#### `ai_analysis.py`
**Purpose:** AI-powered garden detection
- `analyze_garden_likelihood()` - Use OpenAI Vision API to analyze images for vegetable gardens
- Structured output parsing (low/medium/high likelihood)

#### `file_manager.py`
**Purpose:** File system operations and data persistence
- `get_street_folder()` - Generate organized folder paths
- `load_existing_addresses()` - Load previously analyzed addresses
- `save_to_csv()` - Export results with summary statistics

#### `street_finder.py`
**Purpose:** Street discovery using OpenStreetMap
- `get_streets_in_suburb()` - Find multiple streets in a suburb using OSM Nominatim and Overpass APIs

### Main Application

#### `garden_detector.py`
**Purpose:** Main application orchestration
- `GardenDetector` class - Coordinates all modules
- `process_single_street()` - Analyze one street
- `process_multiple_streets()` - Analyze multiple streets
- `main()` - CLI entry point

## Benefits of Modular Structure

### 1. **Separation of Concerns**
- Each module has a single, well-defined responsibility
- Easier to understand what each component does
- Changes to one module don't affect others

### 2. **Reusability**
- Modules can be imported and used independently
- Example: Use `geocoding.py` in other projects that need address lookup

### 3. **Testability**
- Each module can be unit tested in isolation
- Mock external dependencies easily
- Faster test execution

### 4. **Maintainability**
- Bug fixes are localized to specific modules
- Code is easier to navigate and understand
- New developers can focus on one module at a time

### 5. **Extensibility**
- Easy to add new features by extending existing modules
- Can swap implementations (e.g., different AI models)
- Plugin architecture possible

## Usage Examples

### Using Individual Modules

```python
# Use just the geocoding module
from geocoding import enumerate_street_addresses

addresses = enumerate_street_addresses("Main Street", "Albury", 
                                      {'lat': -36.08, 'lng': 146.91})

# Use just the image processing
from image_processing import get_satellite_image
img_data = get_satellite_image(-36.08, 146.91)

# Use just the AI analysis
from ai_analysis import analyze_garden_likelihood
result = analyze_garden_likelihood(img_data, "123 Main St")
```

### Using the Main Application

```bash
# Interactive mode
python garden_detector.py

# Command line mode
python garden_detector.py Albury 20 5
```

## Migration Notes

- **Original file preserved:** `garden_detector_original.py` contains the original monolithic version
- **Backward compatibility:** The main application interface remains the same
- **No API changes:** All command-line options and interactive prompts work identically

## Future Improvements

With this modular structure, you can easily:

1. **Add new data sources** - Create new modules for different cadastre systems
2. **Support different AI models** - Swap out the OpenAI implementation
3. **Add caching** - Implement a caching layer for API calls
4. **Create a web interface** - Import modules into a Flask/FastAPI application
5. **Parallel processing** - Process multiple addresses concurrently
6. **Add logging** - Centralized logging across all modules
7. **Configuration files** - Support YAML/JSON config files

## Module Dependencies

```
garden_detector.py
├── config.py (no dependencies)
├── geocoding.py
│   └── config.py
├── cadastre.py
│   └── config.py
├── image_processing.py
│   ├── config.py
│   └── cadastre.py
├── ai_analysis.py
│   └── config.py
├── file_manager.py
│   └── config.py
└── street_finder.py
    └── config.py
```

## Testing Strategy

Each module can be tested independently:

```python
# Example test for geocoding module
import unittest
from geocoding import find_nearest_house_number

class TestGeocoding(unittest.TestCase):
    def test_find_nearest_house_number(self):
        result = find_nearest_house_number(-36.08, 146.91, 
                                          "Main Street", "Albury")
        self.assertIsInstance(result, int)
```

## Contributing

When adding new features:
1. Identify the appropriate module
2. Keep functions focused and single-purpose
3. Update this README with new functionality
4. Add docstrings to all functions
5. Consider creating a new module if functionality doesn't fit existing ones
