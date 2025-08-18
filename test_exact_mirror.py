#!/usr/bin/env python3
"""Test exactly mirrored circular layout - perfect top/bottom symmetry."""

import os
import glob
import re
import math
from PIL import Image, ImageDraw

def natural_sort_key(filename):
    match = re.search(r'-(\d+)\.tif$', filename)
    if match:
        return int(match.group(1))
    return 0

def create_exact_mirror_layout(num_images, bin_width, bin_height):
    """Create exactly mirrored circular layout."""
    
    # Calculate minimum radius needed
    bin_area = bin_width * bin_height
    total_area = num_images * bin_area
    required_radius = math.sqrt(total_area / math.pi) * 1.1
    canvas_size = int(2 * required_radius)
    center_x = center_y = canvas_size // 2
    
    print(f"Canvas: {canvas_size}x{canvas_size}, Center: ({center_x}, {center_y}), Radius: {required_radius:.1f}")
    
    # Step 1: Calculate the row pattern from center outward to one edge
    half_pattern = []  # Will store (distance_from_center, images_in_row)
    
    # Start from center and work outward  
    for distance in range(0, int(required_radius), bin_height):
        # For this distance from center, what's the circle width?
        if distance <= required_radius:
            x_half_width = math.sqrt(required_radius**2 - distance**2)
            row_width = int(2 * x_half_width)
            images_in_row = max(0, int(row_width / bin_width))
            
            if images_in_row > 0:
                half_pattern.append((distance, images_in_row))
    
    print(f"Half pattern (distance_from_center, images):")
    for dist, imgs in half_pattern:
        print(f"  Distance {dist}: {imgs} images")
    
    # Step 2: Build the complete symmetric pattern
    # Start from the top, go to center, then mirror to bottom
    
    full_rows = []
    
    # Top half (excluding center row)
    for distance, images_count in reversed(half_pattern[1:]):  # Skip distance=0 (center)
        y_pos = center_y - distance - bin_height // 2  # Position above center
        if y_pos >= 0:
            full_rows.append((y_pos, images_count))
    
    # Center row (distance = 0)
    if half_pattern and half_pattern[0][0] == 0:
        center_y_pos = center_y - bin_height // 2
        if center_y_pos >= 0:
            full_rows.append((center_y_pos, half_pattern[0][1]))
    
    # Bottom half (exact mirror of top half)
    top_half_rows = []
    for distance, images_count in reversed(half_pattern[1:]):
        y_pos = center_y - distance - bin_height // 2
        if y_pos >= 0:
            top_half_rows.append((y_pos, images_count))
    
    # Mirror the top half to create bottom half
    for y_pos, images_count in reversed(top_half_rows):
        mirror_distance = center_y - (y_pos + bin_height // 2)  # Distance from center
        mirror_y_pos = center_y + mirror_distance + bin_height // 2
        if mirror_y_pos + bin_height <= canvas_size:
            full_rows.append((mirror_y_pos, images_count))
    
    print(f"\nFull symmetric pattern:")
    for i, (y_pos, img_count) in enumerate(full_rows):
        print(f"  Row {i}: y={y_pos:.0f}, images={img_count}")
    
    # Verify perfect symmetry
    if len(full_rows) >= 2:
        print(f"\nSymmetry verification:")
        mid_point = len(full_rows) // 2
        for i in range(min(5, mid_point)):  # Check first few and last few
            top_imgs = full_rows[i][1]
            bottom_imgs = full_rows[-(i+1)][1]
            print(f"  Row {i} vs Row {len(full_rows)-(i+1)}: {top_imgs} vs {bottom_imgs} {'✓' if top_imgs == bottom_imgs else '✗'}")
    
    # Step 3: Place images
    placements = []
    images_placed = 0
    
    for row_num, (y_position, max_images_in_row) in enumerate(full_rows):
        if images_placed >= num_images:
            break
            
        # Don't exceed remaining images
        actual_images = min(max_images_in_row, num_images - images_placed)
        
        # Center the images in this row
        row_start_x = center_x - (actual_images * bin_width) // 2
        
        for col in range(actual_images):
            x = row_start_x + col * bin_width
            placements.append((x, y_position))
            images_placed += 1
            
            if images_placed >= num_images:
                break
    
    print(f"\nTotal placed: {images_placed}/{num_images}")
    return placements, canvas_size, required_radius

def main():
    # Test with 100 images first
    dataset_path = "/Users/juanmanuelferreradiaz/Downloads/tif200"
    pattern = os.path.join(dataset_path, "*.tif")
    image_files = glob.glob(pattern)
    image_files.sort(key=natural_sort_key)
    
    num_images = 100  # Start with smaller number for testing
    print(f"Testing exact mirror symmetry with {num_images} images")
    
    test_images = image_files[:num_images]
    
    # Create layout
    bin_width, bin_height = 1300, 1900
    placements, canvas_size, radius = create_exact_mirror_layout(num_images, bin_width, bin_height)
    
    # Create visualization
    output_dir = f"exact_mirror_{num_images}_output"
    os.makedirs(output_dir, exist_ok=True)
    
    scale_factor = min(0.15, 4000 / canvas_size)
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
    
    # Draw center line for symmetry reference
    draw.line([0, center_scaled, thumb_width, center_scaled], fill='blue', width=1)
    
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
    
    thumbnail_path = os.path.join(output_dir, f"exact_mirror_{num_images}.tif")
    thumb_canvas.save(thumbnail_path, 'TIFF')
    print(f"Saved: {thumbnail_path}")

if __name__ == "__main__":
    main()