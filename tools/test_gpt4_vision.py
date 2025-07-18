#!/usr/bin/env python3
"""
Test GPT-4 Vision on 1992 LaTeX thesis page
"""

import openai
import base64
import os
from pathlib import Path

def convert_page_to_markdown(image_path, api_key):
    """Convert a single page image to markdown using GPT-4 Vision"""
    
    # Set up OpenAI client
    openai.api_key = api_key
    
    # Read and encode the image
    with open(image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')
    
    # Detailed prompt for 1992 LaTeX conversion
    prompt = """
    Convert this 1992 LaTeX academic page to markdown format with the following requirements:
    
    1. **Text Content**: Preserve exact text content word-for-word
    2. **Inline Equations**: Convert inline mathematical expressions to $...$ format (e.g., $p^*$, $\\omega$, $\\nabla$)
    3. **Block Equations**: Convert display equations to $$...$$ format with proper LaTeX syntax. Put the equation content on the same line as the opening $$ (e.g., $$equation$$ not $$\nequation\n$$). For numbered equations, use align* environment with \\tag{number} for right-justified equation numbers (e.g., $$\\begin{align*} equation \\tag{2.5.1} \\end{align*}$$)
    4. **Section Headers**: Maintain all section headers and numbering (e.g., ## 2.5 Thin shell formulation)
    5. **Mathematical Notation**: Keep all mathematical symbols as LaTeX (Greek letters, operators, etc.)
    6. **Figure References**: Preserve figure references and captions. For figures, use a single image reference like ![Figure X.Y. Caption](attachment:figure-x-y), not separate links for individual labels or symbols within the figure
    7. **Paragraph Structure**: Maintain proper paragraph breaks and formatting
    8. **Historical Context**: This is from 1992 LaTeX typesetting, so account for potential font/symbol variations
    9. **Omit Headers/Footers**: Skip page headers, footers, page numbers, and chapter titles at the top of the page
    
    **Critical**: Distinguish between mathematical variables (should be $...$ format) and regular text.
    For example: "the points are p, p~, and p*" should become "the points are $p$, $p^{\\sim}$, and $p^*$"
    
    Output only the main content as clean markdown with proper LaTeX math formatting. Do not include code block markers.
    """
    
    try:
        # Make the API call
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
            max_tokens=2000
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        return f"Error: {str(e)}"

def main():
    # Check for API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Please set your OPENAI_API_KEY environment variable")
        print("Example: export OPENAI_API_KEY='your-api-key-here'")
        return
    
    # Test image path
    image_path = "test_samples/test_page-042.png"
    
    if not Path(image_path).exists():
        print(f"Image not found: {image_path}")
        return
    
    print("Testing GPT-4 Vision on 1992 LaTeX page...")
    print("This may take 30-60 seconds...")
    
    # Convert the page
    result = convert_page_to_markdown(image_path, api_key)
    
    # Clean up markdown code block formatting if present
    cleaned_result = result.strip()
    
    # Remove markdown code block markers (more robust)
    if cleaned_result.startswith('```markdown'):
        cleaned_result = cleaned_result[11:]
    elif cleaned_result.startswith('```'):
        cleaned_result = cleaned_result[3:]
    
    # Remove trailing code blocks
    if cleaned_result.endswith('```'):
        cleaned_result = cleaned_result[:-3]
    
    # Split into lines and remove any remaining ``` lines
    lines = cleaned_result.split('\n')
    filtered_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped == '```' or stripped == '```markdown':
            continue
        # Skip instruction lines about image paths
        if 'replace' in line.lower() and 'image-path' in line.lower():
            continue
        filtered_lines.append(line)
    
    cleaned_result = '\n'.join(filtered_lines).strip()
    
    # Save result
    output_path = "test_samples/gpt4_vision_result.md"
    with open(output_path, 'w') as f:
        f.write(cleaned_result)
    
    print(f"Results saved to: {output_path}")
    print("\nFirst 500 characters of result:")
    print("-" * 50)
    print(result[:500])
    print("-" * 50)

if __name__ == "__main__":
    main()