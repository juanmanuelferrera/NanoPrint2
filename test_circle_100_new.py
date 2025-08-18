#!/usr/bin/env python3
"""Test new circular layout with 100 images to see the pattern clearly."""

import os
import glob
import re
from datetime import datetime
from PIL import Image, ImageDraw
import logging
from nanofiche_core.packer import NanoFichePacker, EnvelopeSpec, EnvelopeShape
from nanofiche_core.logger import setup_logging

def natural_sort_key(filename):
    match = re.search(r'-(\d+)\.tif$', filename)
    if match:
        return int(match.group(1))
    return 0

def main():
    setup_logging(logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Load 100 images
    dataset_path = "/Users/juanmanuelferreradiaz/Downloads/tif200"
    pattern = os.path.join(dataset_path, "*.tif")
    image_files = glob.glob(pattern)
    image_files.sort(key=natural_sort_key)
    image_files = image_files[:100]
    
    logger.info(f"Testing new circular approach with {len(image_files)} images")
    
    # Test circle with new approach
    packer = NanoFichePacker(1300, 1900)
    envelope_spec = EnvelopeSpec(EnvelopeShape.CIRCLE)
    
    packing_result = packer.pack(len(image_files), envelope_spec)
    logger.info(f"New circle result: {packing_result.rows}x{packing_result.columns} grid")
    logger.info(f"Canvas size: {packing_result.canvas_width}x{packing_result.canvas_height}")
    logger.info(f"Total placements: {len(packing_result.placements)}")
    
    # Create visualization with larger scale
    output_dir = "new_circle_100_output"
    os.makedirs(output_dir, exist_ok=True)
    
    scale_factor = min(0.25, 4000 / max(packing_result.canvas_width, packing_result.canvas_height))
    thumb_width = int(packing_result.canvas_width * scale_factor)
    thumb_height = int(packing_result.canvas_height * scale_factor)
    thumb_canvas = Image.new('RGB', (thumb_width, thumb_height), 'white')
    draw = ImageDraw.Draw(thumb_canvas)
    
    # Draw circle boundary for reference
    center_x_scaled = int(packing_result.canvas_width//2 * scale_factor)
    center_y_scaled = int(packing_result.canvas_height//2 * scale_factor)
    radius_scaled = int(packing_result.canvas_width//2 * scale_factor)
    
    # Draw outer boundary
    draw.ellipse([center_x_scaled-radius_scaled, center_y_scaled-radius_scaled, 
                  center_x_scaled+radius_scaled, center_y_scaled+radius_scaled], 
                 outline='red', width=2)
    
    # Draw working radius (90% boundary)
    working_radius_scaled = int(radius_scaled * 0.9)
    draw.ellipse([center_x_scaled-working_radius_scaled, center_y_scaled-working_radius_scaled, 
                  center_x_scaled+working_radius_scaled, center_y_scaled+working_radius_scaled], 
                 outline='blue', width=2)
    
    # Place images
    for i, (image_file, (x, y)) in enumerate(zip(image_files, packing_result.placements)):
        try:
            scaled_x = int(x * scale_factor)
            scaled_y = int(y * scale_factor)
            scaled_width = max(2, int(1300 * scale_factor))
            scaled_height = max(2, int(1900 * scale_factor))
            
            with Image.open(image_file) as img:
                img_resized = img.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)
                thumb_canvas.paste(img_resized, (scaled_x, scaled_y))
                
            # Number first few images to show order
            if i < 20:
                draw.text((scaled_x, scaled_y), str(i+1), fill='yellow')
                
        except Exception as e:
            logger.error(f"Error processing image {i}: {e}")
    
    thumbnail_path = os.path.join(output_dir, "new_circle_100.tif")
    thumb_canvas.save(thumbnail_path, 'TIFF')
    logger.info(f"Saved: {thumbnail_path}")
    logger.info("Red circle = canvas boundary, Blue circle = 90% working boundary")

if __name__ == "__main__":
    main()