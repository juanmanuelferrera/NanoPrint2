#!/usr/bin/env python3
"""Test circle layout with 1034 images."""

import os
import glob
import re
from datetime import datetime
from PIL import Image
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
    
    # Load all 1034 images
    dataset_path = "/Users/juanmanuelferreradiaz/Downloads/tif200"
    pattern = os.path.join(dataset_path, "*.tif")
    image_files = glob.glob(pattern)
    image_files.sort(key=natural_sort_key)
    image_files = image_files[:1034]
    
    logger.info(f"Testing circle with {len(image_files)} images")
    
    # Test circle with new concentric ring algorithm
    packer = NanoFichePacker(1300, 1900)
    envelope_spec = EnvelopeSpec(EnvelopeShape.CIRCLE)
    
    packing_result = packer.pack(len(image_files), envelope_spec)
    logger.info(f"Circle result: {packing_result.rows}x{packing_result.columns} grid")
    logger.info(f"Canvas size: {packing_result.canvas_width}x{packing_result.canvas_height}")
    logger.info(f"Total placements: {len(packing_result.placements)}")
    
    # Create thumbnail
    output_dir = "gita_test_circle_1:1_output"
    os.makedirs(output_dir, exist_ok=True)
    
    scale_factor = min(1.0, 4000 / max(packing_result.canvas_width, packing_result.canvas_height))
    thumb_width = int(packing_result.canvas_width * scale_factor)
    thumb_height = int(packing_result.canvas_height * scale_factor)
    thumb_canvas = Image.new('RGB', (thumb_width, thumb_height), 'white')
    
    for i, (image_file, (x, y)) in enumerate(zip(image_files, packing_result.placements)):
        if i % 100 == 0:
            logger.info(f"Processing {i+1}/{len(image_files)}")
            
        try:
            scaled_x = int(x * scale_factor)
            scaled_y = int(y * scale_factor)
            scaled_width = int(1300 * scale_factor)
            scaled_height = int(1900 * scale_factor)
            
            with Image.open(image_file) as img:
                img_resized = img.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)
                thumb_canvas.paste(img_resized, (scaled_x, scaled_y))
        except Exception as e:
            logger.error(f"Error: {e}")
    
    thumbnail_path = os.path.join(output_dir, "gita_circle_1:1_thumbnail.tif")
    thumb_canvas.save(thumbnail_path, 'TIFF', compression='lzw', dpi=(200, 200))
    logger.info(f"Saved: {thumbnail_path}")
    
    # Create log file  
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = os.path.join(output_dir, "gita_circle_1:1_test.log")
    with open(log_path, 'w') as log_file:
        log_file.write(f"Gita Dataset Test - Circle 1:1\n")
        log_file.write(f"Timestamp: {timestamp}\n")
        log_file.write(f"Dataset: /Users/juanmanuelferreradiaz/Downloads/tif200\n")
        log_file.write(f"Number of images: {len(image_files)}\n")
        log_file.write(f"Bin dimensions: 1300x1900 pixels\n")
        log_file.write(f"Envelope shape: circle\n")
        log_file.write(f"Aspect ratio: 1.0:1.0\n")
        log_file.write(f"Grid layout: {packing_result.rows}x{packing_result.columns}\n")
        log_file.write(f"Canvas size: {packing_result.canvas_width}x{packing_result.canvas_height}\n")
        log_file.write(f"Sorting method: Arithmetic (numeric)\n")
        log_file.write(f"Placement: Concentric circular rings\n")
        log_file.write(f"Thumbnail scale: {scale_factor:.3f}\n")
        
    logger.info(f"Log saved: {log_path}")

if __name__ == "__main__":
    main()