#!/usr/bin/env python3
"""Final attempt at perfect symmetric circular layout."""

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

def create_perfectly_symmetric_circular_layout(num_images, bin_width, bin_height):
    """Create perfectly symmetric circular layout by pre-calculating all row positions."""
    
    # Calculate minimum radius needed
    bin_area = bin_width * bin_height
    total_area = num_images * bin_area
    required_radius = math.sqrt(total_area / math.pi) * 1.1
    canvas_size = int(2 * required_radius)
    center_x = center_y = canvas_size // 2
    
    print(f"Canvas: {canvas_size}x{canvas_size}, Center: ({center_x}, {center_y}), Radius: {required_radius:.1f}")
    
    # Step 1: Determine all possible row Y positions that fit in the circle
    all_rows = []
    
    # Start from top of canvas and work down
    for y in range(0, canvas_size, bin_height):
        if y + bin_height <= canvas_size:
            row_center_y = y + bin_height // 2
            distance_from_center = abs(row_center_y - center_y)
            
            # Check if this row intersects the circle
            if distance_from_center <= required_radius:
                # Calculate how many images fit in this row
                x_half_width = math.sqrt(required_radius**2 - distance_from_center**2)
                row_width = int(2 * x_half_width)
                images_in_row = max(0, int(row_width / bin_width))
                
                if images_in_row > 0:
                    all_rows.append((y, images_in_row, distance_from_center))
    
    # Step 2: Sort by distance from center to ensure symmetry
    all_rows.sort(key=lambda x: x[2])  # Sort by distance from center
    
    print(f"All rows (y_pos, images, distance_from_center):")
    for i, (y, imgs, dist) in enumerate(all_rows):
        print(f"  Row {i}: y={y}, images={imgs}, distance={dist:.1f}")
    
    # Step 3: Verify symmetry - rows equidistant from center should have same image count
    center_row_index = None
    for i, (y, imgs, dist) in enumerate(all_rows):
        if dist < bin_height // 2:  # This is the center row
            center_row_index = i
            break
    
    if center_row_index is not None:
        print(f"\nCenter row found at index {center_row_index}")
        print("Symmetry check:")
        for i in range(len(all_rows)):
            if i < center_row_index:
                # Check if there's a corresponding row on the other side
                mirror_index = len(all_rows) - 1 - i
                if mirror_index > center_row_index:
                    top_imgs = all_rows[i][1]
                    bottom_imgs = all_rows[mirror_index][1]
                    print(f"  Row {i} ({all_rows[i][1]} imgs) vs Row {mirror_index} ({all_rows[mirror_index][1]} imgs): {'✓' if top_imgs == bottom_imgs else '✗'}")
    
    # Step 4: Place images row by row
    placements = []
    images_placed = 0
    
    for row_num, (y_position, max_images, distance) in enumerate(all_rows):
        if images_placed >= num_images:
            break
            
        # Don't exceed remaining images
        actual_images = min(max_images, num_images - images_placed)
        
        # Center the images in this row
        row_start_x = center_x - (actual_images * bin_width) // 2
        
        print(f"Placing row {row_num}: {actual_images} images at y={y_position}")
        
        for col in range(actual_images):
            x = row_start_x + col * bin_width
            placements.append((x, y_position))
            images_placed += 1
            
            if images_placed >= num_images:
                break
    
    print(f"\nTotal placed: {images_placed}/{num_images}")
    return placements, canvas_size, required_radius, all_rows

def main():
    # Test with smaller number first
    dataset_path = "/Users/juanmanuelferreradiaz/Downloads/tif200"
    pattern = os.path.join(dataset_path, "*.tif")
    image_files = glob.glob(pattern)
    image_files.sort(key=natural_sort_key)
    
    num_images = 50  # Even smaller for clearer testing
    print(f"Testing perfect symmetry with {num_images} images")
    
    test_images = image_files[:num_images]
    
    # Create layout
    bin_width, bin_height = 1300, 1900
    placements, canvas_size, radius, all_rows = create_perfectly_symmetric_circular_layout(num_images, bin_width, bin_height)
    
    # Create visualization
    output_dir = f"final_symmetric_{num_images}_output"
    os.makedirs(output_dir, exist_ok=True)
    
    scale_factor = min(0.2, 4000 / canvas_size)
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
    
    # Draw center line
    draw.line([0, center_scaled, thumb_width, center_scaled], fill='blue', width=1)
    
    # Place images with row numbers
    for i, (image_file, (x, y)) in enumerate(zip(test_images, placements)):
        try:
            scaled_x = int(x * scale_factor)
            scaled_y = int(y * scale_factor)
            scaled_width = max(1, int(bin_width * scale_factor))
            scaled_height = max(1, int(bin_height * scale_factor))
            
            with Image.open(image_file) as img:
                img_resized = img.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)
                thumb_canvas.paste(img_resized, (scaled_x, scaled_y))
                
            # Add image number for first few
            if i < 10:
                draw.text((scaled_x, scaled_y), str(i+1), fill='yellow')
                
        except Exception as e:
            print(f"Error processing image {i}: {e}")
    
    thumbnail_path = os.path.join(output_dir, f"final_symmetric_{num_images}.tif")
    thumb_canvas.save(thumbnail_path, 'TIFF')
    print(f"Saved: {thumbnail_path}")

if __name__ == "__main__":
    main()