#!/usr/bin/env python3
"""Test circular layout using row-by-row approach with variable width per row."""

import os
import glob
import re
import math
from datetime import datetime
from PIL import Image, ImageDraw
import logging

def natural_sort_key(filename):
    match = re.search(r'-(\d+)\.tif$', filename)
    if match:
        return int(match.group(1))
    return 0

def create_circular_rows_layout(num_images, bin_width, bin_height):
    """Create circular layout by placing images row by row with variable width."""
    
    # Step 1: Calculate total area needed
    bin_area = bin_width * bin_height
    total_area = num_images * bin_area
    
    # Step 2: Find minimum radius circle that can contain this area
    # Add some padding for efficient packing
    required_radius = math.sqrt(total_area / math.pi) * 1.1  # 10% padding
    canvas_size = int(2 * required_radius)
    center_x = center_y = canvas_size // 2
    
    print(f"Total area needed: {total_area:,} pixels")
    print(f"Required radius: {required_radius:.1f}")
    print(f"Canvas size: {canvas_size}x{canvas_size}")
    
    placements = []
    images_placed = 0
    
    # Step 3: Go row by row from top to bottom
    current_y = 0
    row_number = 0
    
    while images_placed < num_images and current_y + bin_height <= canvas_size:
        # Calculate the Y position for the center of this row
        row_center_y = current_y + bin_height // 2
        
        # Step 4: Calculate circle width at this Y position
        # Circle equation: x² + y² = r²
        # At this y offset from center: x = ±√(r² - y_offset²)
        y_offset_from_center = abs(row_center_y - center_y)
        
        if y_offset_from_center <= required_radius:
            # Calculate half-width of circle at this Y position
            x_half_width = math.sqrt(required_radius**2 - y_offset_from_center**2)
            row_width = int(2 * x_half_width)
            
            # Step 5: Calculate how many images fit in this row width
            images_in_row = max(0, int(row_width / bin_width))
            
            # Don't exceed remaining images
            images_in_row = min(images_in_row, num_images - images_placed)
            
            if images_in_row > 0:
                # Center the row within the circle width
                row_start_x = center_x - (images_in_row * bin_width) // 2
                
                print(f"Row {row_number}: y={current_y}, width={row_width}, images={images_in_row}, start_x={row_start_x}")
                
                # Place images in this row
                for col in range(images_in_row):
                    x = row_start_x + col * bin_width
                    y = current_y
                    
                    # Ensure within canvas bounds
                    x = max(0, min(x, canvas_size - bin_width))
                    y = max(0, min(y, canvas_size - bin_height))
                    
                    placements.append((x, y))
                    images_placed += 1
                    
                    if images_placed >= num_images:
                        break
        
        current_y += bin_height
        row_number += 1
        
        # Safety check
        if row_number > 100:
            print("Safety break - too many rows")
            break
    
    print(f"Total placed: {images_placed}/{num_images} in {row_number} rows")
    return placements, canvas_size, required_radius

def main():
    logging.basicConfig(level=logging.INFO)
    
    # Load images for testing
    dataset_path = "/Users/juanmanuelferreradiaz/Downloads/tif200"
    pattern = os.path.join(dataset_path, "*.tif")
    image_files = glob.glob(pattern)
    image_files.sort(key=natural_sort_key)
    
    # Test with different numbers
    test_counts = [100, 1034]
    
    for num_images in test_counts:
        print(f"\n=== Testing with {num_images} images ===")
        test_images = image_files[:num_images]
        
        # Create circular row layout
        bin_width, bin_height = 1300, 1900
        placements, canvas_size, radius = create_circular_rows_layout(num_images, bin_width, bin_height)
        
        # Create visualization
        output_dir = f"circular_rows_{num_images}_output"
        os.makedirs(output_dir, exist_ok=True)
        
        scale_factor = min(0.15, 4000 / canvas_size)  # Keep reasonable size
        thumb_width = int(canvas_size * scale_factor)
        thumb_height = int(canvas_size * scale_factor)
        thumb_canvas = Image.new('RGB', (thumb_width, thumb_height), 'white')
        draw = ImageDraw.Draw(thumb_canvas)
        
        # Draw circle boundary for reference
        center_scaled = int(canvas_size//2 * scale_factor)
        radius_scaled = int(radius * scale_factor)
        draw.ellipse([center_scaled-radius_scaled, center_scaled-radius_scaled, 
                      center_scaled+radius_scaled, center_scaled+radius_scaled], 
                     outline='red', width=2)
        
        # Place images
        for i, (image_file, (x, y)) in enumerate(zip(test_images, placements)):
            try:
                scaled_x = int(x * scale_factor)
                scaled_y = int(y * scale_factor)
                scaled_width = max(1, int(bin_width * scale_factor))
                scaled_height = max(1, int(bin_height * scale_factor))
                
                with Image.open(image_file) as img:
                    img_resized = img.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)
                    thumb_canvas.paste(img_resized, (scaled_x, scaled_y))
                    
            except Exception as e:
                print(f"Error processing image {i}: {e}")
        
        thumbnail_path = os.path.join(output_dir, f"circular_rows_{num_images}.tif")
        thumb_canvas.save(thumbnail_path, 'TIFF')
        print(f"Saved: {thumbnail_path}")

if __name__ == "__main__":
    main()