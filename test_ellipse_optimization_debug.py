#!/usr/bin/env python3

"""Debug version to see ellipse optimization in detail"""

import sys
import os
import logging

# Setup detailed logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

sys.path.append(os.path.dirname(__file__))
from nanofiche_core.packer import NanoFichePacker, EnvelopeSpec, EnvelopeShape

def test_ellipse_optimization_debug():
    """Test ellipse packing with detailed optimization debugging."""
    
    # Test with fewer images to see optimization in action
    num_images = 200
    
    # Image dimensions (1:1.29 aspect ratio)
    image_width = 1000
    image_height = 1290
    
    # Create packer
    packer = NanoFichePacker(image_width, image_height)
    
    # Create ellipse spec (3:2 aspect ratio)
    envelope_spec = EnvelopeSpec(
        shape=EnvelopeShape.ELLIPSE,
        aspect_x=3.0,
        aspect_y=2.0
    )
    
    print(f"🔍 DEBUGGING ELLIPSE OPTIMIZATION - {num_images} images")
    print("=" * 60)
    
    # Pack with optimization
    result = packer.pack(num_images, envelope_spec)
    
    print(f"\nFinal result:")
    print(f"Canvas: {result.canvas_width}x{result.canvas_height}")
    print(f"Efficiency: {(num_images * image_width * image_height) / (result.canvas_width * result.canvas_height) * 100:.1f}%")
    print(f"Images placed: {len(result.placements)}")
    
    # Analyze final pattern
    rows = {}
    for x, y in result.placements:
        row_index = y // image_height
        if row_index not in rows:
            rows[row_index] = 0
        rows[row_index] += 1
    
    print(f"\nRow distribution:")
    for row_idx in sorted(rows.keys()):
        count = rows[row_idx]
        print(f"  Row {row_idx}: {count} images")
    
    if rows:
        max_row_idx = max(rows.keys())
        last_row_count = rows[max_row_idx]
        avg_count = sum(rows.values()) / len(rows)
        print(f"\nLast row fill ratio: {last_row_count / avg_count:.2f}")

if __name__ == "__main__":
    test_ellipse_optimization_debug()