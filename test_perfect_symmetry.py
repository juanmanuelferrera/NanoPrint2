#!/usr/bin/env python3
"""Test perfectly symmetric circular layout - top/bottom rows mirror each other exactly."""

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

def create_perfectly_symmetric_layout(num_images, bin_width, bin_height):
    """Create perfectly symmetric circular layout."""
    
    # Calculate minimum radius needed
    bin_area = bin_width * bin_height
    total_area = num_images * bin_area
    required_radius = math.sqrt(total_area / math.pi) * 1.1
    canvas_size = int(2 * required_radius)
    center_x = center_y = canvas_size // 2
    
    print(f"Canvas: {canvas_size}x{canvas_size}, Center: ({center_x}, {center_y}), Radius: {required_radius:.1f}")
    
    # Calculate row pattern from center outward (half circle)
    half_rows = []
    current_y = center_y  # Start at center
    row_index = 0
    
    # Work outward from center to top edge
    while current_y - bin_height >= 0:
        current_y -= bin_height
        row_center_y = current_y + bin_height // 2
        
        # Distance from canvas center
        y_offset = abs(row_center_y - center_y)
        
        if y_offset <= required_radius:
            # Calculate circle width at this Y position
            x_half_width = math.sqrt(required_radius**2 - y_offset**2)
            row_width = int(2 * x_half_width)
            images_in_row = max(0, int(row_width / bin_width))
            
            if images_in_row > 0:
                half_rows.append((current_y, images_in_row))
                row_index += 1
        else:
            break
    
    # Reverse to get top-to-center order
    half_rows.reverse()
    
    # Add center row if it exists
    center_row = None
    center_y_pos = center_y - (center_y % bin_height)  # Align to grid
    if center_y_pos >= 0:
        row_center_y = center_y_pos + bin_height // 2
        y_offset = abs(row_center_y - center_y)
        if y_offset <= required_radius:
            x_half_width = math.sqrt(required_radius**2 - y_offset**2)
            row_width = int(2 * x_half_width)
            images_in_row = max(0, int(row_width / bin_width))
            if images_in_row > 0:
                center_row = (center_y_pos, images_in_row)
    
    # Build complete symmetric pattern
    full_rows = []
    
    # Top half
    full_rows.extend(half_rows)
    
    # Center row (if exists and not already included)
    if center_row and (not half_rows or center_row[0] != half_rows[-1][0]):
        full_rows.append(center_row)
    
    # Bottom half (mirror of top half)
    for y_pos, images_count in reversed(half_rows):
        # Calculate corresponding bottom position
        distance_from_center = center_y - y_pos
        bottom_y = center_y + distance_from_center
        if bottom_y + bin_height <= canvas_size:
            full_rows.append((bottom_y, images_count))
    
    print(f"Row pattern (y_position, images_per_row):")
    for i, (y_pos, img_count) in enumerate(full_rows):
        print(f"  Row {i}: y={y_pos}, images={img_count}")
    
    # Verify symmetry
    if len(full_rows) > 1:
        print(f"Symmetry check:")
        print(f"  Top row: {full_rows[0][1]} images")
        print(f"  Bottom row: {full_rows[-1][1]} images")
        print(f"  Second row: {full_rows[1][1] if len(full_rows) > 1 else 'N/A'} images")
        print(f"  Second-to-last row: {full_rows[-2][1] if len(full_rows) > 1 else 'N/A'} images")
    
    # Place images
    placements = []
    images_placed = 0
    
    for row_num, (y_position, max_images_in_row) in enumerate(full_rows):
        if images_placed >= num_images:
            break
            
        # Don't exceed remaining images
        actual_images = min(max_images_in_row, num_images - images_placed)
        
        # Center the images in this row
        row_start_x = center_x - (actual_images * bin_width) // 2
        
        print(f"Placing row {row_num}: {actual_images} images at y={y_position}")
        
        for col in range(actual_images):
            x = row_start_x + col * bin_width
            placements.append((x, y_position))
            images_placed += 1
            
            if images_placed >= num_images:
                break
    
    print(f"Total placed: {images_placed}/{num_images}")
    return placements, canvas_size, required_radius

def main():
    # Load images
    dataset_path = "/Users/juanmanuelferreradiaz/Downloads/tif200"
    pattern = os.path.join(dataset_path, "*.tif")
    image_files = glob.glob(pattern)
    image_files.sort(key=natural_sort_key)
    
    # Test with different numbers
    for num_images in [100, 1034]:
        print(f"\n{'='*60}")
        print(f"Testing with {num_images} images")
        print(f"{'='*60}")
        
        test_images = image_files[:num_images]
        
        # Create layout
        bin_width, bin_height = 1300, 1900
        placements, canvas_size, radius = create_perfectly_symmetric_layout(num_images, bin_width, bin_height)
        
        # Create visualization
        output_dir = f"perfect_symmetry_{num_images}_output"
        os.makedirs(output_dir, exist_ok=True)
        
        scale_factor = min(0.12, 4000 / canvas_size)
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
        
        thumbnail_path = os.path.join(output_dir, f"perfect_symmetry_{num_images}.tif")
        thumb_canvas.save(thumbnail_path, 'TIFF')
        print(f"Saved: {thumbnail_path}")

if __name__ == "__main__":
    main()