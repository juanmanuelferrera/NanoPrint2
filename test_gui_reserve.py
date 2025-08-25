#!/usr/bin/env python3
"""Quick test of reserved space through the integrated system."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from pathlib import Path
from nanofiche_core.packer import NanoFichePacker, EnvelopeSpec, EnvelopeShape
from nanofiche_core.renderer import NanoFicheRenderer
from nanofiche_core.image_bin import ImageBin
from nanofiche_core.logger import setup_logging

def test_gui_reserve():
    """Test reserved space as it would be used from GUI."""
    setup_logging()
    
    # Simulate GUI inputs
    test_images_path = Path("test_images")
    output_path = Path(".")
    
    # Get test images
    image_files = sorted(test_images_path.glob("*.png"))[:25]
    
    if not image_files:
        print("No test images found!")
        return
    
    print(f"Found {len(image_files)} test images")
    
    # Create image bins with dimensions
    image_bins = []
    for f in image_files:
        from PIL import Image
        with Image.open(f) as img:
            image_bins.append(ImageBin(file_path=f, width=img.width, height=img.height))
    
    # Create packer
    packer = NanoFichePacker(bin_width=1300, bin_height=1900)
    
    # Test with reserved space (simulating GUI input)
    envelope_spec = EnvelopeSpec(
        shape=EnvelopeShape.SQUARE,
        aspect_x=1.0,
        aspect_y=1.0,
        reserve_enabled=True,
        reserve_width=5000,
        reserve_height=5000,
        reserve_position="center"
    )
    
    # Pack images
    packing_result = packer.pack(len(image_bins), envelope_spec)
    
    print(f"\nPacking Result:")
    print(f"  Canvas: {packing_result.canvas_width} x {packing_result.canvas_height}")
    print(f"  Images placed: {len(packing_result.placements)}")
    print(f"  Reserved space: {envelope_spec.reserve_width} x {envelope_spec.reserve_height} at {envelope_spec.reserve_position}")
    
    # Generate preview with reserved space visualization
    renderer = NanoFicheRenderer()
    preview_path = output_path / "test_gui_reserve_preview.tif"
    
    renderer.generate_preview(
        image_bins=image_bins,
        packing_result=packing_result,
        output_path=preview_path,
        max_dimension=2000,
        color=True
    )
    
    print(f"\nPreview saved to: {preview_path}")
    print("Reserved space should be visible as a red overlay in the center")

if __name__ == "__main__":
    test_gui_reserve()