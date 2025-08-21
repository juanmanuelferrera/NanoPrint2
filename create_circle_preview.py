#!/usr/bin/env python3
"""Create a smaller preview of the circle layout."""

from PIL import Image
import os
import sys

def main():
    # Load the image
    input_path = "optimized_circle_output/optimized_circle_test.tif"
    if not os.path.exists(input_path):
        print(f"File not found: {input_path}")
        return
        
    # Open and resize
    with Image.open(input_path) as img:
        # Create a much smaller version
        max_size = 800
        ratio = min(max_size / img.width, max_size / img.height)
        new_width = int(img.width * ratio)
        new_height = int(img.height * ratio)
        
        resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Save as PNG for smaller file size
        output_path = "circle_optimized_preview.png"
        resized.save(output_path, 'PNG')
        print(f"Created small preview: {output_path} ({new_width}x{new_height})")

if __name__ == "__main__":
    main()