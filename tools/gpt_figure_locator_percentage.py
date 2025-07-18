#!/usr/bin/env python3
"""
Use GPT-4 Vision to locate figures using percentage-based coordinates
"""

import openai
import base64
import os
import json
from pathlib import Path

def locate_figure_by_caption_percentage(image_path, figure_caption, api_key):
    """
    Ask GPT-4 Vision to locate a figure using percentage coordinates
    """
    
    openai.api_key = api_key
    
    with open(image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')
    
    prompt = f"""
    I need to extract a technical diagram from this page. 

    STEP 1: Look for the diagram that illustrates: {figure_caption}

    STEP 2: Identify the VISUAL BOUNDARIES of this diagram:
    - Find the leftmost drawn element (line, arrow, or symbol)
    - Find the rightmost drawn element 
    - Find the topmost drawn element
    - Find the bottommost drawn element

    STEP 3: Set tight boundaries around ONLY these visual elements:
    - LEFT edge: just before the leftmost visual element
    - RIGHT edge: just after the rightmost visual element  
    - TOP edge: just above the topmost visual element
    - BOTTOM edge: just below the bottommost visual element

    IMPORTANT: Technical diagrams are typically WIDER than they are tall (rectangular, not square).
    Make sure you capture the full width of the diagram elements.

    CRITICAL: The boundaries should contain ZERO text that forms complete words or sentences. Only include:
    - Lines, curves, shapes
    - Single letter labels (like "p", "E", "D") that are part of the diagram
    - Mathematical symbols and arrows
    - Nothing else

    If you see text like "Figure 2.5" or "The thin shell geometry" - that should be OUTSIDE your boundaries.

    {{
        "found": true/false,
        "percentage_box": [left, top, right, bottom],
        "confidence": "high/medium/low",
        "description": "Visual elements within boundaries"
    }}

    Use numbers only. Respond with JSON only.
    """
    
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=500
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # Clean up any markdown formatting
        if result_text.startswith('```'):
            lines = result_text.split('\n')
            result_text = '\n'.join(lines[1:-1])
        
        try:
            result = json.loads(result_text)
            return result
        except json.JSONDecodeError:
            print(f"Raw response: {result_text}")
            return {"found": False, "error": "Invalid JSON"}
    
    except Exception as e:
        return {"found": False, "error": str(e)}

def extract_figure_with_percentages(image_path, percentage_box, output_path):
    """
    Extract figure using percentage coordinates
    """
    import subprocess
    
    # Get image dimensions
    cmd = ["magick", "identify", "-format", "%w %h", str(image_path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return False
    
    img_width, img_height = map(int, result.stdout.strip().split())
    print(f"Image dimensions: {img_width}x{img_height}")
    
    # Convert percentages to pixels
    left_pct, top_pct, right_pct, bottom_pct = percentage_box
    
    left = int(img_width * left_pct / 100)
    top = int(img_height * top_pct / 100)
    right = int(img_width * right_pct / 100)
    bottom = int(img_height * bottom_pct / 100)
    
    width = right - left
    height = bottom - top
    aspect_ratio = width / height if height > 0 else 0
    
    print(f"Percentage coords: {percentage_box}")
    print(f"Pixel coords: ({left},{top}) to ({right},{bottom})")
    print(f"Crop size: {width}x{height}")
    print(f"Aspect ratio: {aspect_ratio:.2f} (1.0=square, >1.0=wider, <1.0=taller)")
    
    # Warn if aspect ratio seems wrong
    if 0.9 <= aspect_ratio <= 1.1:
        print("⚠️  WARNING: Result is nearly square - technical diagrams are usually rectangular")
    
    # Extract the figure
    crop_spec = f"{width}x{height}+{left}+{top}"
    cmd = ["magick", str(image_path), "-crop", crop_spec, str(output_path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✓ Figure extracted to: {output_path}")
        return True
    else:
        print(f"✗ Extraction failed: {result.stderr}")
        return False

def main():
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python gpt_figure_locator_percentage.py <image> <caption> [output_name]")
        return
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Please set OPENAI_API_KEY environment variable")
        return
    
    image_path = Path(sys.argv[1])
    caption = sys.argv[2]
    output_name = sys.argv[3] if len(sys.argv) > 3 else "figure"
    
    print(f"Analyzing: {image_path}")
    print(f"Looking for: {caption}")
    
    result = locate_figure_by_caption_percentage(image_path, caption, api_key)
    
    if result.get("found"):
        print(f"✓ Found with {result.get('confidence')} confidence")
        print(f"Description: {result.get('description')}")
        
        output_dir = Path("../images")
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / f"{output_name}.png"
        
        if extract_figure_with_percentages(image_path, result["percentage_box"], output_path):
            print(f"Markdown: ![{caption}](images/{output_name}.png)")
        
    else:
        print("✗ Figure not found")
        if "error" in result:
            print(f"Error: {result['error']}")

if __name__ == "__main__":
    main()