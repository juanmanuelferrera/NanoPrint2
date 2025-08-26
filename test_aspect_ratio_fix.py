#!/usr/bin/env python3
"""Test aspect ratio fix for reserve space."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from pathlib import Path
from nanofiche_core.packer import NanoFichePacker, EnvelopeSpec, EnvelopeShape
from nanofiche_core.image_bin import ImageBin
from nanofiche_core.logger import setup_logging
from PIL import Image
import glob

def test_aspect_ratio_fix():
    """Test that reserve space uses user-specified aspect ratio."""
    setup_logging()
    
    # Use small subset for testing
    dataset_path = Path("/Users/juanmanuelferreradiaz/Downloads/tif200")
    if not dataset_path.exists():
        print("Dataset not found! Need /Users/juanmanuelferreradiaz/Downloads/tif200")
        return
        
    image_files = sorted(glob.glob(str(dataset_path / "*.tif")))[:100]  # Small test
    print(f"ASPECT RATIO FIX TEST - {len(image_files)} TIF images")
    print("=" * 60)
    
    # Create image bins
    image_bins = []
    for f in image_files:
        with Image.open(f) as img:
            image_bins.append(ImageBin(file_path=Path(f), width=img.width, height=img.height))
    
    packer = NanoFichePacker(bin_width=1300, bin_height=1900)
    
    # Test 1: Default (should use image aspect ratio 1300:1900 = 0.684)
    print(f"\n🔹 Test 1: Default aspect ratio (image ratio)")
    print("-" * 50)
    
    spec1 = EnvelopeSpec(
        shape=EnvelopeShape.SQUARE,
        reserve_enabled=True,
        reserve_width=5000,
        reserve_height=5000,
        reserve_position="top-left",
        reserve_auto_size=True
    )
    
    result1 = packer.pack(len(image_bins), spec1)
    reserve1_aspect = spec1.reserve_width / spec1.reserve_height
    image_aspect = 1300 / 1900
    
    print(f"Canvas: {result1.canvas_width}x{result1.canvas_height}")
    print(f"Reserve: {spec1.reserve_width}x{spec1.reserve_height}")
    print(f"Reserve aspect ratio: {reserve1_aspect:.3f}")
    print(f"Image aspect ratio: {image_aspect:.3f}")
    print(f"Match: {'✓' if abs(reserve1_aspect - image_aspect) < 0.01 else '✗'}")
    
    # Test 2: Custom aspect ratio (2:1 - wide)
    print(f"\n🔹 Test 2: Custom wide aspect ratio (2:1)")
    print("-" * 50)
    
    spec2 = EnvelopeSpec(
        shape=EnvelopeShape.SQUARE,
        reserve_enabled=True,
        reserve_width=5000,
        reserve_height=5000,
        reserve_position="top-left",
        reserve_auto_size=True,
        reserve_aspect_x=2.0,
        reserve_aspect_y=1.0
    )
    
    result2 = packer.pack(len(image_bins), spec2)
    reserve2_aspect = spec2.reserve_width / spec2.reserve_height
    target_aspect = 2.0 / 1.0
    
    print(f"Canvas: {result2.canvas_width}x{result2.canvas_height}")
    print(f"Reserve: {spec2.reserve_width}x{spec2.reserve_height}")
    print(f"Reserve aspect ratio: {reserve2_aspect:.3f}")
    print(f"Target aspect ratio: {target_aspect:.3f}")
    print(f"Match: {'✓' if abs(reserve2_aspect - target_aspect) < 0.01 else '✗'}")
    
    # Test 3: Custom aspect ratio (1:2 - tall)
    print(f"\n🔹 Test 3: Custom tall aspect ratio (1:2)")
    print("-" * 50)
    
    spec3 = EnvelopeSpec(
        shape=EnvelopeShape.SQUARE,
        reserve_enabled=True,
        reserve_width=5000,
        reserve_height=5000,
        reserve_position="top-left",
        reserve_auto_size=True,
        reserve_aspect_x=1.0,
        reserve_aspect_y=2.0
    )
    
    result3 = packer.pack(len(image_bins), spec3)
    reserve3_aspect = spec3.reserve_width / spec3.reserve_height
    target_aspect3 = 1.0 / 2.0
    
    print(f"Canvas: {result3.canvas_width}x{result3.canvas_height}")
    print(f"Reserve: {spec3.reserve_width}x{spec3.reserve_height}")
    print(f"Reserve aspect ratio: {reserve3_aspect:.3f}")
    print(f"Target aspect ratio: {target_aspect3:.3f}")
    print(f"Match: {'✓' if abs(reserve3_aspect - target_aspect3) < 0.01 else '✗'}")
    
    # Summary
    print(f"\n📊 ASPECT RATIO FIX SUMMARY")
    print("=" * 60)
    print(f"{'Test':<20} {'Reserve Ratio':<15} {'Target Ratio':<15} {'Status'}")
    print("-" * 60)
    
    status1 = '✓ PASS' if abs(reserve1_aspect - image_aspect) < 0.01 else '✗ FAIL'
    status2 = '✓ PASS' if abs(reserve2_aspect - target_aspect) < 0.01 else '✗ FAIL'
    status3 = '✓ PASS' if abs(reserve3_aspect - target_aspect3) < 0.01 else '✗ FAIL'
    
    print(f"{'Default (image)':<20} {reserve1_aspect:<14.3f} {image_aspect:<14.3f} {status1}")
    print(f"{'Wide (2:1)':<20} {reserve2_aspect:<14.3f} {target_aspect:<14.3f} {status2}")
    print(f"{'Tall (1:2)':<20} {reserve3_aspect:<14.3f} {target_aspect3:<14.3f} {status3}")
    
    all_passed = all([
        abs(reserve1_aspect - image_aspect) < 0.01,
        abs(reserve2_aspect - target_aspect) < 0.01,
        abs(reserve3_aspect - target_aspect3) < 0.01
    ])
    
    print(f"\n🏆 OVERALL RESULT: {'✓ ALL TESTS PASSED' if all_passed else '✗ SOME TESTS FAILED'}")
    
    return all_passed

if __name__ == "__main__":
    test_aspect_ratio_fix()