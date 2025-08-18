#!/usr/bin/env python3
"""
Test script for Gita dataset variations with different envelope shapes.
Based on test requirements:
- Use 1,034 images from Gita dataset (1240x1840 actual dimensions)
- Set bin dimensions of 1300x1900
- Test 4 envelope variations with arithmetic sorting
- Generate thumbnail previews for each variation
"""

import os
import glob
import re
from datetime import datetime
from PIL import Image
import logging
from nanofiche_core.packer import NanoFichePacker, EnvelopeSpec, EnvelopeShape
from nanofiche_core.logger import setup_logging

def natural_sort_key(filename):
    """
    Sort filenames by numeric value instead of alphabetic.
    Extracts number from filename like 'edition-123.tif' -> 123
    """
    match = re.search(r'-(\d+)\.tif$', filename)
    if match:
        return int(match.group(1))
    return 0

def load_gita_images(dataset_path, max_count=1034):
    """Load and validate Gita dataset images with arithmetic sorting."""
    logger = logging.getLogger(__name__)
    
    # Get all TIFF files
    pattern = os.path.join(dataset_path, "*.tif")
    image_files = glob.glob(pattern)
    
    # Sort by numeric value (arithmetic sort)
    image_files.sort(key=natural_sort_key)
    
    # Limit to requested count
    if len(image_files) > max_count:
        image_files = image_files[:max_count]
    
    logger.info(f"Found {len(image_files)} images in dataset")
    logger.info(f"First file: {os.path.basename(image_files[0])}")
    logger.info(f"Last file: {os.path.basename(image_files[-1])}")
    
    # Validate first few images
    for i in range(min(3, len(image_files))):
        try:
            with Image.open(image_files[i]) as img:
                logger.info(f"Image {i+1}: {img.size[0]}x{img.size[1]} pixels")
        except Exception as e:
            logger.error(f"Error loading {image_files[i]}: {e}")
    
    return image_files

def run_envelope_test(image_files, envelope_spec, test_name, bin_width=1300, bin_height=1900):
    """Run a single envelope test variation."""
    logger = logging.getLogger(__name__)
    
    logger.info(f"=== Running {test_name} Test ===")
    
    # Setup output directory
    output_dir = f"gita_test_{test_name.lower().replace(' ', '_')}_output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize packer
    packer = NanoFichePacker(bin_width, bin_height)
    
    # Calculate packing
    num_bins = len(image_files)
    packing_result = packer.pack(num_bins, envelope_spec)
    
    logger.info(f"Packing result: {packing_result.rows}x{packing_result.columns} grid")
    logger.info(f"Canvas size: {packing_result.canvas_width}x{packing_result.canvas_height}")
    
    # Generate thumbnail
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    thumbnail_path = os.path.join(output_dir, f"gita_{test_name.lower().replace(' ', '_')}_thumbnail.tif")
    log_path = os.path.join(output_dir, f"gita_{test_name.lower().replace(' ', '_')}_test.log")
    
    # Create thumbnail (reduced size for preview)
    max_thumb_size = 4000
    scale_factor = min(1.0, max_thumb_size / max(packing_result.canvas_width, packing_result.canvas_height))
    
    thumb_width = int(packing_result.canvas_width * scale_factor)
    thumb_height = int(packing_result.canvas_height * scale_factor)
    thumb_canvas = Image.new('RGB', (thumb_width, thumb_height), 'white')
    
    # Place images in thumbnail
    for i, (image_file, (x, y)) in enumerate(zip(image_files, packing_result.placements)):
        if i % 100 == 0:
            logger.info(f"Processing image {i+1}/{len(image_files)}")
        
        try:
            # Scale placement coordinates
            scaled_x = int(x * scale_factor)
            scaled_y = int(y * scale_factor)
            scaled_width = int(bin_width * scale_factor)
            scaled_height = int(bin_height * scale_factor)
            
            # Load and resize image
            with Image.open(image_file) as img:
                # Resize image to fit scaled bin
                img_resized = img.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)
                
                # Paste into canvas
                thumb_canvas.paste(img_resized, (scaled_x, scaled_y))
                
        except Exception as e:
            logger.error(f"Error processing {image_file}: {e}")
    
    # Save thumbnail
    thumb_canvas.save(thumbnail_path, 'TIFF', compression='lzw', dpi=(200, 200))
    logger.info(f"Saved thumbnail: {thumbnail_path}")
    
    # Log test parameters
    with open(log_path, 'w') as log_file:
        log_file.write(f"Gita Dataset Test - {test_name}\n")
        log_file.write(f"Timestamp: {timestamp}\n")
        log_file.write(f"Dataset: /Users/juanmanuelferreradiaz/Downloads/tif200\n")
        log_file.write(f"Number of images: {len(image_files)}\n")
        log_file.write(f"Bin dimensions: {bin_width}x{bin_height} pixels\n")
        log_file.write(f"Envelope shape: {envelope_spec.shape.value}\n")
        log_file.write(f"Aspect ratio: {envelope_spec.aspect_x}:{envelope_spec.aspect_y}\n")
        log_file.write(f"Grid layout: {packing_result.rows}x{packing_result.columns}\n")
        log_file.write(f"Canvas size: {packing_result.canvas_width}x{packing_result.canvas_height}\n")
        log_file.write(f"Sorting method: Arithmetic (numeric)\n")
        log_file.write(f"Placement: Left to right, top to bottom\n")
        log_file.write(f"Thumbnail scale: {scale_factor:.3f}\n")
        log_file.write(f"Output files:\n")
        log_file.write(f"  - {thumbnail_path}\n")
        log_file.write(f"  - {log_path}\n")
    
    return {
        'test_name': test_name,
        'thumbnail_path': thumbnail_path,
        'log_path': log_path,
        'packing_result': packing_result,
        'num_images': len(image_files)
    }

def main():
    """Main test function."""
    # Setup logging
    setup_logging(logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Gita dataset envelope variation tests")
    
    # Dataset path
    dataset_path = "/Users/juanmanuelferreradiaz/Downloads/tif200"
    
    # Load images with arithmetic sorting
    image_files = load_gita_images(dataset_path, max_count=1034)
    
    if not image_files:
        logger.error("No images found in dataset")
        return
    
    # Bin dimensions as specified
    bin_width = 1300
    bin_height = 1900
    
    # Test variations
    test_variations = [
        {
            'name': 'Rectangle 1.29:1',
            'spec': EnvelopeSpec(EnvelopeShape.RECTANGLE, aspect_x=1.29, aspect_y=1.0)
        },
        {
            'name': 'Square 1:1', 
            'spec': EnvelopeSpec(EnvelopeShape.SQUARE)
        },
        {
            'name': 'Ellipse 1.29:1',
            'spec': EnvelopeSpec(EnvelopeShape.ELLIPSE, aspect_x=1.29, aspect_y=1.0)
        },
        {
            'name': 'Circle 1:1',
            'spec': EnvelopeSpec(EnvelopeShape.CIRCLE)
        }
    ]
    
    results = []
    
    # Run each test variation
    for variation in test_variations:
        try:
            result = run_envelope_test(
                image_files, 
                variation['spec'], 
                variation['name'],
                bin_width, 
                bin_height
            )
            results.append(result)
            logger.info(f"Completed {variation['name']} test")
            
        except Exception as e:
            logger.error(f"Error in {variation['name']} test: {e}")
    
    # Summary
    logger.info("=== Test Summary ===")
    for result in results:
        logger.info(f"{result['test_name']}: {result['num_images']} images")
        logger.info(f"  Thumbnail: {result['thumbnail_path']}")
        logger.info(f"  Log: {result['log_path']}")
    
    logger.info("All tests completed!")

if __name__ == "__main__":
    main()