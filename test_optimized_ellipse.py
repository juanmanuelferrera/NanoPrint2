#!/usr/bin/env python3

import sys
import os
import glob
import re
import logging
from pathlib import Path

# Add the nanofiche_core directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'nanofiche_core'))

from nanofiche_core.logger import setup_logging
from nanofiche_core.packer import NanoFichePacker
from nanofiche_core.renderer import NanoFicheRenderer

def natural_sort_key(filename):
    """Extract numeric part from filename for proper sorting (1, 2, ... 10, 11, ...)"""
    match = re.search(r'-(\d+)\.tif', filename)
    if match:
        return int(match.group(1))
    return 0

def test_optimized_ellipse():
    # Setup logging
    setup_logging()
    logger = logging.getLogger("test_optimized_ellipse")
    
    # Dataset path
    dataset_path = "/Users/juanmanuelferreradiaz/Downloads/tif200"
    
    # Get list of images and sort numerically
    image_files = glob.glob(os.path.join(dataset_path, "*.tif"))
    image_files.sort(key=natural_sort_key)
    
    # Limit to 1034 images
    image_files = image_files[:1034]
    
    logger.info(f"Processing {len(image_files)} images for optimized ellipse test")
    
    # Create output directory
    output_dir = "optimized_ellipse_output"
    Path(output_dir).mkdir(exist_ok=True)
    
    # Create packer with bin dimensions
    bin_width = 1300
    bin_height = 1900
    packer = NanoFichePacker(bin_width, bin_height)
    
    # Generate layout for ellipse with 1.0:1.29 aspect ratio (portrait)
    envelope_shape = "ellipse"
    aspect_ratio = (1.0, 1.29)
    
    logger.info(f"Generating {envelope_shape} layout with aspect ratio {aspect_ratio[0]}:{aspect_ratio[1]}")
    
    # Create envelope spec
    from nanofiche_core.packer import EnvelopeSpec, EnvelopeShape
    envelope_spec = EnvelopeSpec(EnvelopeShape.ELLIPSE, aspect_ratio[0], aspect_ratio[1])
    
    # Calculate grid dimensions
    packing_result = packer.pack(len(image_files), envelope_spec)
    
    rows, cols = packing_result.rows, packing_result.columns
    canvas_width, canvas_height = packing_result.canvas_width, packing_result.canvas_height
    
    logger.info(f"Grid: {rows}x{cols}, Canvas: {canvas_width}x{canvas_height}")
    
    # Generate TIFF
    renderer = NanoFicheRenderer()
    output_filename = f"{output_dir}/optimized_ellipse_test.tif"
    
    # Create image bins from file paths
    from nanofiche_core.image_bin import ImageBin
    image_bins = []
    for i, image_path in enumerate(image_files):
        # Use bin dimensions for all images (this is a test)
        image_bin = ImageBin(
            file_path=Path(image_path),
            width=bin_width,
            height=bin_height,
            index=i
        )
        image_bins.append(image_bin)
    
    # Generate the full resolution TIFF and thumbnail
    output_path = Path(output_filename)
    log_path = Path(f"{output_dir}/optimized_ellipse_test.log")
    
    thumbnail_result = renderer.generate_thumbnail_tiff(
        image_bins=image_bins,
        packing_result=packing_result,
        output_path=output_path,
        log_path=log_path,
        project_name="optimized_ellipse_test",
        approved=False
    )
    
    if thumbnail_result:
        logger.info(f"Thumbnail generated: {thumbnail_result}")
        
        # Write test log
        log_filename = f"{output_dir}/optimized_ellipse_test.log"
        with open(log_filename, 'w') as log_file:
            log_file.write(f"Optimized Ellipse Test\n")
            log_file.write(f"Timestamp: {thumbnail_result.split('_')[-1].split('.')[0]}\n")
            log_file.write(f"Dataset: {dataset_path}\n")
            log_file.write(f"Number of images: {len(image_files)}\n")
            log_file.write(f"Bin dimensions: {bin_width}x{bin_height} pixels\n")
            log_file.write(f"Envelope shape: {envelope_shape}\n")
            log_file.write(f"Aspect ratio: {aspect_ratio[0]}:{aspect_ratio[1]}\n")
            log_file.write(f"Grid layout: {rows}x{cols}\n")
            log_file.write(f"Canvas size: {canvas_width}x{canvas_height}\n")
            log_file.write(f"Sorting method: Arithmetic (numeric)\n")
            log_file.write(f"Placement: Left to right, top to bottom\n")
            log_file.write(f"Optimization: Minimal envelope-to-image area ratio\n")
            log_file.write(f"Output files:\n")
            log_file.write(f"  - {thumbnail_result}\n")
            log_file.write(f"  - {log_filename}\n")
        
        logger.info(f"Test completed. Check {output_dir}/ for results")
        print(f"Optimized ellipse test completed. Thumbnail: {thumbnail_result}")
        return True
    else:
        logger.error("Failed to generate thumbnail")
        return False

if __name__ == "__main__":
    success = test_optimized_ellipse()
    sys.exit(0 if success else 1)