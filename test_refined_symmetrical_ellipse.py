#!/usr/bin/env python3

import sys
import os
import glob
import re
import logging
import math
from pathlib import Path

# Add the nanofiche_core directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'nanofiche_core'))

from nanofiche_core.logger import setup_logging
from nanofiche_core.renderer import NanoFicheRenderer
from nanofiche_core.image_bin import ImageBin
from nanofiche_core.packer import EnvelopeShape

def natural_sort_key(filename):
    """Extract numeric part from filename for proper sorting (1, 2, ... 10, 11, ...)"""
    match = re.search(r'-(\d+)\.tif', filename)
    if match:
        return int(match.group(1))
    return 0

def analyze_row_distribution(a, b, bin_width, bin_height):
    """Analyze the distribution of images across rows in an ellipse."""
    center_x, center_y = a, b
    max_rows = int(2 * b / bin_height)
    
    row_counts = []
    for row_idx in range(max_rows):
        y = center_y - b + (row_idx + 0.5) * bin_height
        y_offset = y - center_y
        
        if abs(y_offset) >= b:
            continue
            
        width_factor = math.sqrt(max(0, 1 - (y_offset / b) ** 2))
        row_half_width = a * width_factor * 0.95
        bins_in_row = int(2 * row_half_width / bin_width)
        
        # Ensure even number for symmetry
        if bins_in_row > 1 and bins_in_row % 2 == 1:
            bins_in_row -= 1
            
        if bins_in_row > 0:
            row_counts.append(bins_in_row)
    
    if len(row_counts) < 2:
        return 0, 0, float('inf')
    
    top_row = row_counts[0]
    bottom_row = row_counts[-1]
    ratio = max(top_row, bottom_row) / max(min(top_row, bottom_row), 1)
    
    return top_row, bottom_row, ratio

def find_refined_symmetrical_ellipse(num_bins, target_aspect_x, target_aspect_y, bin_width, bin_height):
    """Find ellipse with refined symmetry using 1% steps when close to balance."""
    
    target_aspect_ratio = target_aspect_x / target_aspect_y
    best_arrangement = None
    best_score = float('inf')
    
    # Phase 1: Coarse search with larger steps
    sqrt_bins = math.sqrt(num_bins)
    for cols in range(int(sqrt_bins * 0.4), int(sqrt_bins * 2.5) + 1):
        rows = math.ceil(num_bins / cols)
        
        # Calculate required ellipse size with some margin
        grid_width = cols * bin_width
        grid_height = rows * bin_height
        margin = 1.15
        
        if target_aspect_ratio >= 1:
            required_a = max(grid_width / 2 * margin, grid_height / 2 * margin * target_aspect_ratio)
            required_b = required_a / target_aspect_ratio
        else:
            required_b = max(grid_height / 2 * margin, grid_width / 2 * margin / target_aspect_ratio)
            required_a = required_b * target_aspect_ratio
        
        # Test capacity and row distribution
        placements = test_refined_placement_capacity(num_bins, required_a, required_b, bin_width, bin_height)
        
        if len(placements) >= num_bins:
            top_row, bottom_row, ratio = analyze_row_distribution(required_a, required_b, bin_width, bin_height)
            ellipse_area = math.pi * required_a * required_b
            
            # Score based on area and symmetry (prefer bottom > top)
            symmetry_penalty = 0
            if top_row > bottom_row:
                symmetry_penalty = 1000000  # Heavy penalty for top > bottom
            else:
                symmetry_penalty = ratio * 10000  # Penalty for imbalance
            
            score = ellipse_area + symmetry_penalty
            
            if score < best_score:
                best_score = score
                best_arrangement = {
                    'grid': (rows, cols),
                    'ellipse_params': (required_a, required_b),
                    'area': ellipse_area,
                    'top_row': top_row,
                    'bottom_row': bottom_row,
                    'ratio': ratio
                }
    
    if best_arrangement is None:
        # Fallback
        side = math.ceil(sqrt_bins)
        margin = 1.3
        if target_aspect_ratio >= 1:
            required_a = side * bin_width / 2 * margin
            required_b = required_a / target_aspect_ratio
        else:
            required_b = side * bin_height / 2 * margin
            required_a = required_b * target_aspect_ratio
        return (side, side), (required_a, required_b)
    
    # Phase 2: Fine refinement with 1% steps if we're within 2x ratio
    if best_arrangement['ratio'] <= 2.0:
        logger = logging.getLogger("refinement")
        logger.info(f"Entering fine refinement phase. Current ratio: {best_arrangement['ratio']:.2f}")
        
        base_a, base_b = best_arrangement['ellipse_params']
        
        # Try fine adjustments to ellipse size (1% steps)
        for scale_factor in [i/100.0 for i in range(100, 120)]:  # 1.00 to 1.19 in 1% steps
            test_a = base_a * scale_factor
            test_b = base_b * scale_factor
            
            placements = test_refined_placement_capacity(num_bins, test_a, test_b, bin_width, bin_height)
            
            if len(placements) >= num_bins:
                top_row, bottom_row, ratio = analyze_row_distribution(test_a, test_b, bin_width, bin_height)
                ellipse_area = math.pi * test_a * test_b
                
                # Strong preference for bottom > top, then minimize ratio
                symmetry_penalty = 0
                if top_row > bottom_row:
                    symmetry_penalty = 1000000
                else:
                    symmetry_penalty = ratio * 10000
                
                score = ellipse_area + symmetry_penalty
                
                if score < best_score:
                    best_score = score
                    best_arrangement = {
                        'grid': best_arrangement['grid'],
                        'ellipse_params': (test_a, test_b),
                        'area': ellipse_area,
                        'top_row': top_row,
                        'bottom_row': bottom_row,
                        'ratio': ratio
                    }
                    logger.info(f"Improved: scale={scale_factor:.2f}, top={top_row}, bottom={bottom_row}, ratio={ratio:.2f}")
    
    return best_arrangement['grid'], best_arrangement['ellipse_params']

def test_refined_placement_capacity(num_bins, a, b, bin_width, bin_height):
    """Test placement capacity with refined algorithm."""
    center_x, center_y = a, b
    max_rows = int(2 * b / bin_height)
    
    placements = []
    bins_placed = 0
    
    for row_idx in range(max_rows):
        if bins_placed >= num_bins:
            break
            
        y = center_y - b + (row_idx + 0.5) * bin_height
        y_offset = y - center_y
        
        if abs(y_offset) >= b:
            continue
            
        width_factor = math.sqrt(max(0, 1 - (y_offset / b) ** 2))
        row_half_width = a * width_factor * 0.95
        bins_in_row = int(2 * row_half_width / bin_width)
        
        # Ensure even number for symmetry
        if bins_in_row > 1 and bins_in_row % 2 == 1:
            bins_in_row -= 1
            
        if bins_in_row > 0:
            for col in range(bins_in_row):
                if bins_placed >= num_bins:
                    break
                    
                x = center_x - (bins_in_row * bin_width) / 2 + col * bin_width
                bin_center_x = x + bin_width // 2
                bin_center_y = y + bin_height // 2
                ellipse_test = ((bin_center_x - center_x) / a) ** 2 + ((bin_center_y - center_y) / b) ** 2
                
                if ellipse_test <= 0.98:
                    placements.append((int(x), int(y)))
                    bins_placed += 1
    
    return placements

def generate_refined_symmetrical_placements(num_bins, center_x, center_y, a, b, bin_width, bin_height):
    """Generate placements with refined symmetry."""
    max_rows = int(2 * b / bin_height)
    
    placements = []
    bins_placed = 0
    
    for row_idx in range(max_rows):
        if bins_placed >= num_bins:
            break
            
        y = center_y - b + (row_idx + 0.5) * bin_height
        y_offset = y - center_y
        
        if abs(y_offset) >= b:
            continue
            
        width_factor = math.sqrt(max(0, 1 - (y_offset / b) ** 2))
        row_half_width = a * width_factor * 0.95
        bins_in_row = int(2 * row_half_width / bin_width)
        
        # Ensure even number for symmetry
        if bins_in_row > 1 and bins_in_row % 2 == 1:
            bins_in_row -= 1
            
        if bins_in_row > 0:
            start_x = center_x - (bins_in_row * bin_width) / 2
            
            for col in range(bins_in_row):
                if bins_placed >= num_bins:
                    break
                    
                x = start_x + col * bin_width
                bin_center_x = x + bin_width // 2
                bin_center_y = y + bin_height // 2
                ellipse_test = ((bin_center_x - center_x) / a) ** 2 + ((bin_center_y - center_y) / b) ** 2
                
                if ellipse_test <= 0.98:
                    placements.append((int(x), int(y)))
                    bins_placed += 1
    
    return placements

def test_refined_symmetrical_ellipse():
    # Setup logging
    setup_logging()
    logger = logging.getLogger("test_refined_symmetrical_ellipse")
    
    # Dataset path
    dataset_path = "/Users/juanmanuelferreradiaz/Downloads/tif200"
    
    # Get list of images and sort numerically
    image_files = glob.glob(os.path.join(dataset_path, "*.tif"))
    image_files.sort(key=natural_sort_key)
    
    # Limit to 1034 images
    image_files = image_files[:1034]
    
    logger.info(f"Processing {len(image_files)} images for refined symmetrical ellipse test")
    
    # Create output directory
    output_dir = "refined_symmetrical_ellipse_output"
    Path(output_dir).mkdir(exist_ok=True)
    
    # Bin dimensions
    bin_width = 1300
    bin_height = 1900
    
    # Ellipse parameters (portrait 1.0:1.29 aspect ratio)
    aspect_x = 1.0
    aspect_y = 1.29
    
    logger.info(f"Target aspect ratio: {aspect_x}:{aspect_y}")
    
    # Find refined symmetrical ellipse
    (rows, cols), (a, b) = find_refined_symmetrical_ellipse(
        len(image_files), aspect_x, aspect_y, bin_width, bin_height
    )
    
    canvas_width = int(2 * a)
    canvas_height = int(2 * b)
    center_x = canvas_width // 2
    center_y = canvas_height // 2
    
    # Analyze final row distribution
    top_row, bottom_row, ratio = analyze_row_distribution(a, b, bin_width, bin_height)
    
    logger.info(f"Optimal grid: {rows}x{cols}")
    logger.info(f"Ellipse parameters: a={a:.1f}, b={b:.1f}")
    logger.info(f"Canvas size: {canvas_width}x{canvas_height}")
    logger.info(f"Top row images: {top_row}, Bottom row images: {bottom_row}")
    logger.info(f"Top/Bottom ratio: {ratio:.2f}")
    logger.info(f"Bottom > Top: {bottom_row > top_row}")
    
    # Generate refined symmetrical placements
    placements = generate_refined_symmetrical_placements(
        len(image_files), center_x, center_y, a, b, bin_width, bin_height
    )
    
    logger.info(f"Generated {len(placements)} placements for {len(image_files)} images")
    logger.info(f"Fill efficiency: {len(placements)/len(image_files)*100:.1f}%")
    
    # Create mock packing result
    class MockPackingResult:
        def __init__(self, rows, cols, placements, canvas_width, canvas_height):
            self.rows = rows
            self.columns = cols
            self.canvas_width = canvas_width
            self.canvas_height = canvas_height
            self.placements = placements
            self.envelope_shape = EnvelopeShape.ELLIPSE
            self.total_bins = len(placements)
            self.bin_width = bin_width
            self.bin_height = bin_height
    
    packing_result = MockPackingResult(rows, cols, placements, canvas_width, canvas_height)
    
    # Generate TIFF
    renderer = NanoFicheRenderer()
    output_filename = f"{output_dir}/refined_symmetrical_ellipse_test.tif"
    
    # Create image bins from file paths
    image_bins = []
    for i, image_path in enumerate(image_files[:len(placements)]):
        image_bin = ImageBin(
            file_path=Path(image_path),
            width=bin_width,
            height=bin_height,
            index=i
        )
        image_bins.append(image_bin)
    
    # Generate the full resolution TIFF and thumbnail
    output_path = Path(output_filename)
    log_path = Path(f"{output_dir}/refined_symmetrical_ellipse_test.log")
    
    thumbnail_result = renderer.generate_thumbnail_tiff(
        image_bins=image_bins,
        packing_result=packing_result,
        output_path=output_path,
        log_path=log_path,
        project_name="refined_symmetrical_ellipse_test",
        approved=False
    )
    
    if thumbnail_result:
        logger.info(f"Thumbnail generated: {thumbnail_result}")
        
        # Write test log
        log_filename = f"{output_dir}/refined_symmetrical_ellipse_test.log"
        with open(log_filename, 'w') as log_file:
            log_file.write(f"Refined Symmetrical Ellipse Test\n")
            log_file.write(f"Timestamp: {thumbnail_result.split('_')[-1].split('.')[0]}\n")
            log_file.write(f"Dataset: {dataset_path}\n")
            log_file.write(f"Number of images: {len(image_files)}\n")
            log_file.write(f"Images placed: {len(placements)}\n")
            log_file.write(f"Fill efficiency: {len(placements)/len(image_files)*100:.1f}%\n")
            log_file.write(f"Bin dimensions: {bin_width}x{bin_height} pixels\n")
            log_file.write(f"Envelope shape: ellipse (refined symmetrical)\n")
            log_file.write(f"Target aspect ratio: {aspect_x}:{aspect_y}\n")
            log_file.write(f"Optimal grid: {rows}x{cols}\n")
            log_file.write(f"Ellipse radii: a={a:.1f}, b={b:.1f}\n")
            log_file.write(f"Canvas size: {canvas_width}x{canvas_height}\n")
            log_file.write(f"Top row images: {top_row}\n")
            log_file.write(f"Bottom row images: {bottom_row}\n")
            log_file.write(f"Top/Bottom ratio: {ratio:.2f}\n")
            log_file.write(f"Bottom > Top: {bottom_row > top_row}\n")
            log_file.write(f"Refinement: 1% envelope steps when within 2x ratio\n")
            log_file.write(f"Output files:\n")
            log_file.write(f"  - {thumbnail_result}\n")
            log_file.write(f"  - {log_filename}\n")
        
        logger.info(f"Test completed. Check {output_dir}/ for results")
        print(f"Refined symmetrical ellipse test completed. Thumbnail: {thumbnail_result}")
        print(f"Top: {top_row}, Bottom: {bottom_row}, Ratio: {ratio:.2f}, Bottom>Top: {bottom_row > top_row}")
        print(f"Fill efficiency: {len(placements)/len(image_files)*100:.1f}% ({len(placements)}/{len(image_files)} images)")
        return True
    else:
        logger.error("Failed to generate thumbnail")
        return False

if __name__ == "__main__":
    success = test_refined_symmetrical_ellipse()
    sys.exit(0 if success else 1)