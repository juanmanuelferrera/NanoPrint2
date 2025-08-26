#!/usr/bin/env python3

"""Test 100% bottom fill algorithm with detailed debugging"""

import sys
import os
import logging

# Setup detailed logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

sys.path.append(os.path.dirname(__file__))
from nanofiche_core.packer import NanoFichePacker, EnvelopeSpec, EnvelopeShape

def test_bottom_fill_debug():
    """Test 100% bottom fill with debugging."""
    
    # Test with moderate number of images
    num_images = 500
    
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
    
    print(f"🔍 TESTING 100% BOTTOM FILL - {num_images} images")
    print("=" * 60)
    
    # Pack with 100% bottom fill optimization
    result = packer.pack(num_images, envelope_spec)
    
    print(f"\nFinal result:")
    print(f"Canvas: {result.canvas_width}x{result.canvas_height}")
    print(f"Images placed: {len(result.placements)}")
    
    # Analyze final pattern
    rows = {}
    for x, y in result.placements:
        row_index = y // image_height
        if row_index not in rows:
            rows[row_index] = 0
        rows[row_index] += 1
    
    if rows:
        print(f"\nRow distribution:")
        for row_idx in sorted(rows.keys()):
            count = rows[row_idx]
            print(f"  Row {row_idx}: {count} images")
        
        # Check bottom fill
        canvas_height = result.canvas_height
        row_env_y = canvas_height - image_height
        row_image_y = max(y for x, y in result.placements)
        
        print(f"\nBottom fill analysis:")
        print(f"  row_env_y (envelope bottom): {row_env_y}")
        print(f"  row_image_y (actual bottom): {row_image_y}")
        print(f"  Difference: {row_env_y - row_image_y} pixels")
        
        if abs(row_env_y - row_image_y) <= image_height // 2:
            print("  ✅ Images reach envelope bottom!")
        else:
            print("  ❌ Images don't reach envelope bottom")

if __name__ == "__main__":
    test_bottom_fill_debug()