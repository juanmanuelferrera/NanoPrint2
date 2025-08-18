#!/usr/bin/env python3
"""Test symmetric circular layout - ensuring top/bottom rows have same number of images."""

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

def create_symmetric_circular_layout(num_images, bin_width, bin_height):
    """Create symmetric circular layout with same number of images in top/bottom rows."""
    
    # Step 1: Calculate total area needed
    bin_area = bin_width * bin_height
    total_area = num_images * bin_area
    
    # Step 2: Find minimum radius circle - with padding for efficient packing
    required_radius = math.sqrt(total_area / math.pi) * 1.1
    canvas_size = int(2 * required_radius)
    center_x = center_y = canvas_size // 2
    
    print(f"Total area needed: {total_area:,} pixels")
    print(f"Required radius: {required_radius:.1f}")
    print(f"Canvas size: {canvas_size}x{canvas_size}")
    print(f"Center at: ({center_x}, {center_y})")
    
    # Step 3: Calculate how many complete rows we can fit
    max_rows = int(canvas_size / bin_height)
    
    # Step 4: Calculate row information symmetrically
    row_info = []  # Will store (y_position, images_in_row)
    
    # Start from the center and work outward
    center_row = max_rows // 2
    
    for offset in range(max_rows // 2 + 1):  # From center to edge
        # Calculate for rows above and below center
        for direction in [-1, 1] if offset > 0 else [0]:  # Center row only once
            if direction == 0:  # Center row
                row_index = center_row
            else:
                row_index = center_row + direction * offset
                
            if 0 <= row_index < max_rows:
                y_position = row_index * bin_height
                row_center_y = y_position + bin_height // 2
                
                # Calculate distance from canvas center
                y_offset_from_center = abs(row_center_y - center_y)
                
                if y_offset_from_center <= required_radius:
                    # Calculate circle width at this Y position
                    x_half_width = math.sqrt(required_radius**2 - y_offset_from_center**2)
                    row_width = int(2 * x_half_width)
                    images_in_row = max(0, int(row_width / bin_width))
                    
                    if images_in_row > 0:
                        row_info.append((y_position, images_in_row, row_index))
    
    # Sort by row index for proper order
    row_info.sort(key=lambda x: x[2])
    
    print(f"Total rows: {len(row_info)}")
    
    # Step 5: Place images row by row
    placements = []
    images_placed = 0
    
    for row_num, (y_position, images_in_row, row_index) in enumerate(row_info):
        if images_placed >= num_images:
            break
            
        # Don't exceed remaining images
        actual_images = min(images_in_row, num_images - images_placed)
        
        # Center the row
        row_start_x = center_x - (actual_images * bin_width) // 2
        
        print(f"Row {row_num} (index {row_index}): y={y_position}, max_images={images_in_row}, actual={actual_images}")
        
        # Place images in this row
        for col in range(actual_images):
            x = row_start_x + col * bin_width
            
            # Ensure within canvas bounds
            x = max(0, min(x, canvas_size - bin_width))
            y = max(0, min(y_position, canvas_size - bin_height))
            
            placements.append((x, y))
            images_placed += 1
    
    print(f"Total placed: {images_placed}/{num_images}")
    
    # Verify symmetry
    if len(row_info) > 1:
        top_row_images = row_info[0][1]  # First row
        bottom_row_images = row_info[-1][1]  # Last row
        print(f"Symmetry check: Top row = {top_row_images}, Bottom row = {bottom_row_images}")
        if top_row_images != bottom_row_images:
            print("WARNING: Not symmetric!")
    
    return placements, canvas_size, required_radius

def main():
    logging.basicConfig(level=logging.INFO)
    
    # Load images
    dataset_path = "/Users/juanmanuelferreradiaz/Downloads/tif200"
    pattern = os.path.join(dataset_path, "*.tif")
    image_files = glob.glob(pattern)
    image_files.sort(key=natural_sort_key)
    
    # Test with 1034 images
    num_images = 1034
    print(f"\n=== Testing symmetric circular layout with {num_images} images ===")
    test_images = image_files[:num_images]
    
    # Create symmetric circular layout
    bin_width, bin_height = 1300, 1900
    placements, canvas_size, radius = create_symmetric_circular_layout(num_images, bin_width, bin_height)
    
    # Create visualization
    output_dir = f"symmetric_circular_{num_images}_output"
    os.makedirs(output_dir, exist_ok=True)
    
    scale_factor = min(0.1, 4000 / canvas_size)  # Keep reasonable size
    thumb_width = int(canvas_size * scale_factor)
    thumb_height = int(canvas_size * scale_factor)
    thumb_canvas = Image.new('RGB', (thumb_width, thumb_height), 'white')
    draw = ImageDraw.Draw(thumb_canvas)
    
    # Draw circle boundary
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
    
    thumbnail_path = os.path.join(output_dir, f"symmetric_circular_{num_images}.tif")
    thumb_canvas.save(thumbnail_path, 'TIFF')
    print(f"Saved: {thumbnail_path}")

if __name__ == "__main__":
    main()