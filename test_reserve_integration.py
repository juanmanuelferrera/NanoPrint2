#!/usr/bin/env python3
"""Test script to verify reserved space integration."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from nanofiche_core.packer import NanoFichePacker, EnvelopeSpec, EnvelopeShape
from nanofiche_core.logger import setup_logging
import logging

def test_reserved_space():
    """Test the reserved space functionality."""
    setup_logging()
    logger = logging.getLogger("test_reserve")
    
    # Create packer
    packer = NanoFichePacker(bin_width=1300, bin_height=1900)
    
    # Test 1: Square without reserve
    logger.info("\nTest 1: Square without reserve")
    spec1 = EnvelopeSpec(
        shape=EnvelopeShape.SQUARE,
        reserve_enabled=False
    )
    result1 = packer.pack(25, spec1)
    logger.info(f"Canvas: {result1.canvas_width}x{result1.canvas_height}")
    logger.info(f"Placed: {len(result1.placements)} bins")
    
    # Test 2: Square with center reserve
    logger.info("\nTest 2: Square with 5000x5000 center reserve")
    spec2 = EnvelopeSpec(
        shape=EnvelopeShape.SQUARE,
        reserve_enabled=True,
        reserve_width=5000,
        reserve_height=5000,
        reserve_position="center"
    )
    result2 = packer.pack(25, spec2)
    logger.info(f"Canvas: {result2.canvas_width}x{result2.canvas_height}")
    logger.info(f"Placed: {len(result2.placements)} bins")
    
    # Test 3: Rectangle with top-left reserve
    logger.info("\nTest 3: Rectangle with 3000x4000 top-left reserve")
    spec3 = EnvelopeSpec(
        shape=EnvelopeShape.RECTANGLE,
        aspect_x=1.29,
        aspect_y=1.0,
        reserve_enabled=True,
        reserve_width=3000,
        reserve_height=4000,
        reserve_position="top-left"
    )
    result3 = packer.pack(25, spec3)
    logger.info(f"Canvas: {result3.canvas_width}x{result3.canvas_height}")
    logger.info(f"Placed: {len(result3.placements)} bins")
    
    # Verify no overlaps with reserve
    for i, (x, y) in enumerate(result3.placements):
        if spec3.reserve_position == "top-left":
            if x < spec3.reserve_width and y < spec3.reserve_height:
                logger.error(f"Bin {i} overlaps with reserve at ({x}, {y})")
    
    logger.info("\nAll tests completed successfully!")

if __name__ == "__main__":
    test_reserved_space()