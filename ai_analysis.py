"""
AI analysis module for Garden Detector application.
Handles OpenAI Vision API calls for garden detection in satellite images.
"""

import base64
import json
from typing import Dict
from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL


# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)


def analyze_garden_likelihood(image_data: bytes, address: str) -> Dict[str, str]:
    """
    Use OpenAI Vision API to analyze an image for vegetable garden presence.
    
    Args:
        image_data: Satellite image as bytes
        address: Address being analyzed (for context)
        
    Returns:
        Dictionary with 'reasoning' and 'likelihood' keys
    """
    # Convert image to base64
    base64_image = base64.b64encode(image_data).decode('utf-8')
    
    prompt = """Analyze this satellite/aerial image of a suburban property and determine the likelihood 
that there is a vegetable garden present. You are looking at just one property

IMPORTANT: The property being analyzed is marked with a RED BOUNDARY LINE showing the property borders. 
Focus your analysis on the area within the red boundary.

Look for:
- Organized rows of plants
- Raised garden beds
- Rectangular or organized garden patches
- Dark soil areas with regular patterns
- Areas that appear to be cultivated (different from lawn)

First, provide your reasoning about what you observe in the property. Then, determine the likelihood level.

Likelihood levels:
- low: No clear evidence of a vegetable garden, mostly lawn/pavement/natural vegetation
- medium: Some signs that could be a garden (organized plantings, possible raised beds) but not definitive
- high: Clear evidence of vegetable garden (visible rows, raised beds, organized cultivation)"""
    
    # Define the function schema for structured output
    tools = [
        {
            "type": "function",
            "function": {
                "name": "analyze_garden",
                "description": "Analyze a satellite image to determine the likelihood of a vegetable garden being present",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reasoning": {
                            "type": "string",
                            "description": "Detailed reasoning about what is observed in the property, including visible features, vegetation patterns, and any signs of cultivation or garden structures"
                        },
                        "likelihood": {
                            "type": "string",
                            "enum": ["low", "medium", "high"],
                            "description": "The likelihood level of a vegetable garden being present: low (no clear evidence), medium (some signs but not definitive), or high (clear evidence)"
                        }
                    },
                    "required": ["reasoning", "likelihood"]
                }
            }
        }
    ]
    
    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            tools=tools,
            tool_choice={"type": "function", "function": {"name": "analyze_garden"}}
        )
        
        # Extract the function call response
        tool_call = response.choices[0].message.tool_calls[0]
        result = json.loads(tool_call.function.arguments)
        
        reasoning = result.get('reasoning', 'No reasoning provided')
        likelihood = result.get('likelihood', 'low').lower()
        
        # Validate the likelihood
        if likelihood not in ['low', 'medium', 'high']:
            print(f"  Unexpected likelihood value: {likelihood}, defaulting to 'low'")
            likelihood = 'low'
        
        return {
            'reasoning': reasoning,
            'likelihood': likelihood
        }
            
    except Exception as e:
        print(f"  Error analyzing image: {e}")
        return {
            'reasoning': 'Error occurred during analysis',
            'likelihood': 'low'
        }
