# NSW Cadastre API - Quick Reference Card

## Base URL
```
https://maps.six.nsw.gov.au/arcgis/rest/services/public/NSW_Cadastre/MapServer
```

## Common Endpoints

### 1. Get Property at Point
```python
import requests

url = "https://maps.six.nsw.gov.au/arcgis/rest/services/public/NSW_Cadastre/MapServer/identify"
params = {
    'geometry': '146.9166,-36.0833',  # lon,lat
    'geometryType': 'esriGeometryPoint',
    'sr': 4326,
    'layers': 'all',
    'tolerance': 5,
    'mapExtent': '146.91,-36.09,146.92,-36.08',  # bbox
    'imageDisplay': '400,400,96',
    'returnGeometry': 'true',
    'f': 'json'
}
response = requests.get(url, params=params)
data = response.json()
property_boundary = data['results'][0]['geometry']['rings']
```

### 2. Export Map Image
```python
url = "https://maps.six.nsw.gov.au/arcgis/rest/services/public/NSW_Cadastre/MapServer/export"
params = {
    'bbox': '146.91,-36.09,146.92,-36.08',  # minLon,minLat,maxLon,maxLat
    'bboxSR': 4326,
    'size': '1024,768',
    'imageSR': 4326,
    'format': 'png32',
    'transparent': 'true',
    'f': 'image'
}
response = requests.get(url, params=params)
with open('cadastre.png', 'wb') as f:
    f.write(response.content)
```

### 3. Search by Property ID
```python
url = "https://maps.six.nsw.gov.au/arcgis/rest/services/public/NSW_Cadastre/MapServer/find"
params = {
    'searchText': 'LOT 1',
    'contains': 'true',
    'searchFields': '',
    'sr': 4326,
    'returnGeometry': 'true',
    'f': 'json'
}
response = requests.get(url, params=params)
properties = response.json()['results']
```

## Spatial References
- **4326** = WGS84 (standard lat/lon)
- **3857** = Web Mercator

## Image Formats
- **png32** = 32-bit PNG with transparency
- **png24** = 24-bit PNG
- **jpg** = JPEG

## Response Structure

### Identify Response
```json
{
  "results": [
    {
      "layerId": 0,
      "layerName": "Cadastre",
      "value": "12345",
      "displayFieldName": "lotidstring",
      "attributes": {
        "lotidstring": "LOT 1 DP 123456",
        ...
      },
      "geometry": {
        "rings": [
          [
            [146.9166, -36.0833],
            [146.9167, -36.0834],
            ...
          ]
        ]
      }
    }
  ]
}
```

## NSW Bounds
- **Longitude:** 141.0 to 154.0
- **Latitude:** -37.5 to -28.0

## Limits
- **Max Image Size:** 4096 x 4096 pixels
- **Max Records:** 1000 per query
- **Timeout:** 30-60 seconds recommended

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| 400 | Invalid parameters | Check bbox order, SR codes |
| 500 | Server error | Retry with backoff |
| Empty results | No property at location | Increase tolerance |
| Timeout | Large area/slow network | Reduce bbox or increase timeout |

## Quick Template

```python
import requests
from typing import Optional, Dict

class CadastreAPI:
    BASE_URL = "https://maps.six.nsw.gov.au/arcgis/rest/services/public/NSW_Cadastre/MapServer"
    
    @staticmethod
    def get_property(lon: float, lat: float) -> Optional[Dict]:
        offset = 0.005
        bbox = f"{lon-offset},{lat-offset},{lon+offset},{lat+offset}"
        
        response = requests.get(
            f"{CadastreAPI.BASE_URL}/identify",
            params={
                'geometry': f"{lon},{lat}",
                'geometryType': 'esriGeometryPoint',
                'sr': 4326,
                'layers': 'all',
                'tolerance': 5,
                'mapExtent': bbox,
                'imageDisplay': '400,400,96',
                'returnGeometry': 'true',
                'f': 'json'
            },
            timeout=30
        )
        
        data = response.json()
        return data['results'][0] if data.get('results') else None

# Usage
api = CadastreAPI()
property_data = api.get_property(146.9166, -36.0833)
if property_data:
    print(f"Found: {property_data['attributes']['lotidstring']}")
    boundary = property_data['geometry']['rings']
```

## Installation

```bash
pip install requests pillow shapely
```

## Useful Coordinates (Albury, NSW)

| Location | Longitude | Latitude |
|----------|-----------|----------|
| Albury CBD | 146.9166 | -36.0833 |
| Test Point 1 | 146.9200 | -36.0850 |
| Test Point 2 | 146.9150 | -36.0800 |
