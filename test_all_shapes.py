#!/usr/bin/env python3
"""Quick test for all shapes with 100 images."""

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

def test_shape(shape_spec, shape_name, image_files):
    logger = logging.getLogger(__name__)
    
    packer = NanoFichePacker(1300, 1900)
    packing_result = packer.pack(len(image_files), shape_spec)
    
    logger.info(f"{shape_name} result: {packing_result.rows}x{packing_result.columns} grid")
    logger.info(f"  Canvas: {packing_result.canvas_width}x{packing_result.canvas_height}")
    logger.info(f"  Placements: {len(packing_result.placements)}")
    
    # Create small thumbnail
    output_dir = f"test_{shape_name.lower().replace(' ', '_')}_output"
    os.makedirs(output_dir, exist_ok=True)
    
    scale_factor = 0.05
    thumb_width = int(packing_result.canvas_width * scale_factor)
    thumb_height = int(packing_result.canvas_height * scale_factor)
    thumb_canvas = Image.new('RGB', (thumb_width, thumb_height), 'white')
    
    for i, (image_file, (x, y)) in enumerate(zip(image_files, packing_result.placements)):
        try:
            scaled_x = int(x * scale_factor)
            scaled_y = int(y * scale_factor)
            scaled_width = max(1, int(1300 * scale_factor))
            scaled_height = max(1, int(1900 * scale_factor))
            
            with Image.open(image_file) as img:
                img_resized = img.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)
                thumb_canvas.paste(img_resized, (scaled_x, scaled_y))
        except Exception as e:
            pass
    
    thumbnail_path = os.path.join(output_dir, f"{shape_name.lower().replace(' ', '_')}_test.tif")
    thumb_canvas.save(thumbnail_path, 'TIFF')
    logger.info(f"  Saved: {thumbnail_path}")

def main():
    setup_logging(logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Load 100 images for quick test
    dataset_path = "/Users/juanmanuelferreradiaz/Downloads/tif200"
    pattern = os.path.join(dataset_path, "*.tif")
    image_files = glob.glob(pattern)
    image_files.sort(key=natural_sort_key)
    image_files = image_files[:100]
    
    logger.info(f"Testing all shapes with {len(image_files)} images")
    
    # Test all shapes
    test_shape(EnvelopeSpec(EnvelopeShape.RECTANGLE, aspect_x=1.29, aspect_y=1.0), "Rectangle 1.29:1", image_files)
    test_shape(EnvelopeSpec(EnvelopeShape.SQUARE), "Square 1:1", image_files)
    test_shape(EnvelopeSpec(EnvelopeShape.ELLIPSE, aspect_x=1.29, aspect_y=1.0), "Ellipse 1.29:1", image_files)
    test_shape(EnvelopeSpec(EnvelopeShape.CIRCLE), "Circle 1:1", image_files)
    
    logger.info("All tests completed!")

if __name__ == "__main__":
    main()