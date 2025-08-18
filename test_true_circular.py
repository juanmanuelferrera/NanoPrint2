#!/usr/bin/env python3
"""Test true circular visual arrangement."""

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

def create_circular_pattern(num_images, canvas_size, bin_width, bin_height):
    """Create circular pattern with rows that form concentric circles."""
    placements = []
    center_x = center_y = canvas_size // 2
    max_radius = canvas_size // 2 * 0.8
    
    bins_placed = 0
    
    # Calculate how many concentric circles we need
    bin_diagonal = math.sqrt(bin_width**2 + bin_height**2)
    ring_spacing = bin_diagonal * 0.8
    max_rings = int(max_radius / ring_spacing)
    
    print(f"Creating {max_rings} concentric rings, spacing: {ring_spacing}")
    
    # Place center image
    if bins_placed < num_images:
        x = center_x - bin_width // 2
        y = center_y - bin_height // 2
        placements.append((x, y))
        bins_placed += 1
        print(f"Placed center image at ({x}, {y})")
    
    # Create concentric rings
    for ring in range(1, max_rings + 1):
        if bins_placed >= num_images:
            break
            
        ring_radius = ring * ring_spacing
        if ring_radius > max_radius:
            break
            
        # Calculate circumference and how many images fit
        circumference = 2 * math.pi * ring_radius
        images_in_ring = max(1, int(circumference / (bin_width * 1.2)))  # Some spacing between images
        
        # Don't exceed remaining images
        images_in_ring = min(images_in_ring, num_images - bins_placed)
        
        print(f"Ring {ring}: radius={ring_radius:.1f}, images={images_in_ring}")
        
        # Place images around the ring
        for i in range(images_in_ring):
            angle = (2 * math.pi * i) / images_in_ring
            
            x = center_x + int(ring_radius * math.cos(angle)) - bin_width // 2
            y = center_y + int(ring_radius * math.sin(angle)) - bin_height // 2
            
            # Ensure within canvas
            x = max(0, min(x, canvas_size - bin_width))
            y = max(0, min(y, canvas_size - bin_height))
            
            placements.append((x, y))
            bins_placed += 1
            
            if bins_placed >= num_images:
                break
    
    print(f"Total placed: {bins_placed}/{num_images}")
    return placements

def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Load 100 images for testing
    dataset_path = "/Users/juanmanuelferreradiaz/Downloads/tif200"
    pattern = os.path.join(dataset_path, "*.tif")
    image_files = glob.glob(pattern)
    image_files.sort(key=natural_sort_key)
    image_files = image_files[:100]
    
    print(f"Testing true circular pattern with {len(image_files)} images")
    
    # Create circular arrangement
    bin_width, bin_height = 1300, 1900
    canvas_size = 25000  # Large canvas for circular arrangement
    
    placements = create_circular_pattern(len(image_files), canvas_size, bin_width, bin_height)
    
    # Create visualization
    output_dir = "true_circular_output"
    os.makedirs(output_dir, exist_ok=True)
    
    scale_factor = 0.15
    thumb_width = int(canvas_size * scale_factor)
    thumb_height = int(canvas_size * scale_factor)
    thumb_canvas = Image.new('RGB', (thumb_width, thumb_height), 'white')
    draw = ImageDraw.Draw(thumb_canvas)
    
    # Draw circle boundary for reference
    center_scaled = int(canvas_size//2 * scale_factor)
    radius_scaled = int(canvas_size//2 * 0.8 * scale_factor)
    draw.ellipse([center_scaled-radius_scaled, center_scaled-radius_scaled, 
                  center_scaled+radius_scaled, center_scaled+radius_scaled], 
                 outline='red', width=2)
    
    # Place images
    for i, (image_file, (x, y)) in enumerate(zip(image_files, placements)):
        try:
            scaled_x = int(x * scale_factor)
            scaled_y = int(y * scale_factor)
            scaled_width = max(2, int(bin_width * scale_factor))
            scaled_height = max(2, int(bin_height * scale_factor))
            
            with Image.open(image_file) as img:
                img_resized = img.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)
                thumb_canvas.paste(img_resized, (scaled_x, scaled_y))
                
            # Number the first few images for debugging
            if i < 20:
                draw.text((scaled_x, scaled_y), str(i+1), fill='yellow')
                
        except Exception as e:
            print(f"Error processing image {i}: {e}")
    
    thumbnail_path = os.path.join(output_dir, "true_circular_test.tif")
    thumb_canvas.save(thumbnail_path, 'TIFF')
    print(f"Saved: {thumbnail_path}")

if __name__ == "__main__":
    main()