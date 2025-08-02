#!/usr/bin/env python3
"""
GPT-4 Vision API utilities for thesis conversion workflow.

This module provides standardized interfaces for GPT-4 Vision API calls
including image encoding, prompt templates, and response handling.
"""

import base64
import openai
import time
import shutil
from pathlib import Path
from progress_utils import print_progress, time_operation


def encode_images_for_vision(image_paths, show_progress=True):
    """
    Encode PNG images as base64 for GPT-4 Vision API.

    Converts local image files to the base64 format required by the
    OpenAI Vision API. Handles multiple images for multi-page processing.

    Args:
        image_paths (list): List of Path objects pointing to PNG files
        show_progress (bool): Whether to show encoding progress

    Returns:
        list: List of image content dictionaries for Vision API
    """
    if show_progress:
        print_progress("Encoding images for GPT-4 Vision...")

    image_contents = []

    for i, image_path in enumerate(image_paths):
        if show_progress:
            print_progress(f"Encoding page image", i+1, len(image_paths))

        try:
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
                image_contents.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{base64_image}"
                    }
                })
        except Exception as e:
            print_progress(f"- Error encoding {image_path}: {e}")

    return image_contents


def call_gpt_vision_api(prompt, image_contents, model="gpt-4o", max_tokens=16000, api_key=None):
    """
    Make a GPT-4 Vision API call with proper error handling and timing.

    Standardized interface for all GPT-4 Vision API calls in the thesis
    conversion workflow. Includes timing, error handling, and progress reporting.

    Args:
        prompt (str): Text prompt for the Vision API
        image_contents (list): List of encoded image dictionaries
        model (str): OpenAI model to use (default "gpt-4o")
        max_tokens (int): Maximum tokens in response (default 16000)
        api_key (str, optional): OpenAI API key (uses openai.api_key if None)

    Returns:
        str: API response content, or error message starting with "Error:"
    """
    if api_key:
        openai.api_key = api_key

    # Prepare message content
    content = [{"type": "text", "text": prompt}] + image_contents

    print_progress("Sending to GPT-4 Vision API...")
    print_progress("Processing with AI (estimated 30-60 seconds)...")

    try:
        with time_operation("GPT-4 Vision API call"):
            response = openai.chat.completions.create(
                model=model,
                messages=[{
                    "role": "user",
                    "content": content
                }],
                max_tokens=max_tokens
            )

        return response.choices[0].message.content

    except Exception as e:
        print_progress(f"- GPT-4 Vision API error: {str(e)}")
        return f"Error: {str(e)}"






def cleanup_temp_directory(temp_dir):
    """
    Clean up temporary directory used for image processing.

    Safely removes temporary directories created during PDF to image
    conversion, with error handling for cleanup failures.

    Args:
        temp_dir (str): Path to temporary directory to remove
    """
    try:
        print_progress("Cleaning up temporary files...")
        shutil.rmtree(temp_dir, ignore_errors=True)
    except Exception as e:
        print_progress(f"- Warning: Could not clean up {temp_dir}: {e}")


def clean_markdown_output(result):
    """
    Clean markdown output from GPT-4 Vision API responses.

    Removes common markdown code block markers that the API sometimes
    includes in responses, ensuring clean markdown content.

    Args:
        result (str): Raw response from GPT-4 Vision API

    Returns:
        str: Cleaned markdown content
    """
    cleaned_result = result.strip()

    # Remove markdown code block markers
    if cleaned_result.startswith('```markdown'):
        cleaned_result = cleaned_result[11:]
    elif cleaned_result.startswith('```'):
        cleaned_result = cleaned_result[3:]

    if cleaned_result.endswith('```'):
        cleaned_result = cleaned_result[:-3]

    return cleaned_result.strip()