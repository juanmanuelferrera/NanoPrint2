#!/usr/bin/env python3
"""Debug circle layout with just a few images to see what's happening."""

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
    
    # Load just 50 images for debugging
    dataset_path = "/Users/juanmanuelferreradiaz/Downloads/tif200"
    pattern = os.path.join(dataset_path, "*.tif")
    image_files = glob.glob(pattern)
    image_files.sort(key=natural_sort_key)
    image_files = image_files[:50]  # Just 50 for debugging
    
    logger.info(f"DEBUG: Testing circle with {len(image_files)} images")
    
    # Test circle
    packer = NanoFichePacker(1300, 1900)
    envelope_spec = EnvelopeSpec(EnvelopeShape.CIRCLE)
    
    packing_result = packer.pack(len(image_files), envelope_spec)
    logger.info(f"DEBUG: Circle result: {packing_result.rows}x{packing_result.columns} grid")
    logger.info(f"DEBUG: Canvas size: {packing_result.canvas_width}x{packing_result.canvas_height}")
    logger.info(f"DEBUG: Total placements: {len(packing_result.placements)}")
    logger.info(f"DEBUG: Center should be at: {packing_result.canvas_width//2}, {packing_result.canvas_height//2}")
    logger.info(f"DEBUG: Radius should be: {packing_result.canvas_width//2}")
    
    # Print first few placements to see pattern
    logger.info("DEBUG: First 10 placements:")
    for i, (x, y) in enumerate(packing_result.placements[:10]):
        center_x, center_y = packing_result.canvas_width//2, packing_result.canvas_height//2
        distance = ((x + 1300//2 - center_x)**2 + (y + 1900//2 - center_y)**2)**0.5
        logger.info(f"  Image {i+1}: ({x}, {y}) - distance from center: {distance:.1f}")
    
    # Create debug thumbnail with circle overlay
    output_dir = "debug_circle_output"
    os.makedirs(output_dir, exist_ok=True)
    
    scale_factor = 0.2  # Bigger for debugging
    thumb_width = int(packing_result.canvas_width * scale_factor)
    thumb_height = int(packing_result.canvas_height * scale_factor)
    thumb_canvas = Image.new('RGB', (thumb_width, thumb_height), 'white')
    draw = ImageDraw.Draw(thumb_canvas)
    
    # Draw circle boundary for reference
    center_x_scaled = int(packing_result.canvas_width//2 * scale_factor)
    center_y_scaled = int(packing_result.canvas_height//2 * scale_factor)
    radius_scaled = int(packing_result.canvas_width//2 * scale_factor)
    
    # Draw outer circle boundary
    draw.ellipse([center_x_scaled-radius_scaled, center_y_scaled-radius_scaled, 
                  center_x_scaled+radius_scaled, center_y_scaled+radius_scaled], 
                 outline='red', width=2)
    
    # Draw 75% circle boundary (where bins should fit)
    radius_75_scaled = int(radius_scaled * 0.75)
    draw.ellipse([center_x_scaled-radius_75_scaled, center_y_scaled-radius_75_scaled, 
                  center_x_scaled+radius_75_scaled, center_y_scaled+radius_75_scaled], 
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
        except Exception as e:
            logger.error(f"Error processing image {i}: {e}")
    
    thumbnail_path = os.path.join(output_dir, "debug_circle.tif")
    thumb_canvas.save(thumbnail_path, 'TIFF')
    logger.info(f"DEBUG: Saved debug thumbnail: {thumbnail_path}")
    logger.info("DEBUG: Red circle = outer boundary, Blue circle = 75% boundary where bins should fit")

if __name__ == "__main__":
    main()