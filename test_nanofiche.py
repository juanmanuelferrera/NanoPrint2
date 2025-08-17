#!/usr/bin/env python3
"""
Test script for NanoFiche Image Prep functionality.
Creates test images and runs the packing algorithm.
"""

import sys
sys.path.insert(0, '.')

from pathlib import Path
from PIL import Image, ImageDraw
from nanofiche_core import NanoFichePacker, EnvelopeShape, EnvelopeSpec, ImageBin, NanoFicheRenderer
from nanofiche_core.logger import setup_logging
import logging

def create_test_images(count=10):
    """Create test images for demonstration."""
    test_dir = Path("test_images")
    test_dir.mkdir(exist_ok=True)
    
    image_files = []
    for i in range(count):
        # Create simple test image
        img = Image.new('RGB', (400, 500), color=(i*25 % 255, 100, 200))
        draw = ImageDraw.Draw(img)
        draw.text((50, 50), f"Image {i+1}", fill='white')
        
        # Save
        img_path = test_dir / f"test_image_{i+1:03d}.png"
        img.save(img_path)
        image_files.append(img_path)
        print(f"Created {img_path}")
    
    return image_files

def test_packing():
    """Test the packing algorithm with different shapes."""
    setup_logging(logging.INFO)
    
    # Create test images
    print("Creating test images...")
    image_files = create_test_images(25)
    
    # Create image bins
    image_bins = [ImageBin(f, 1800, 2300, i) for i, f in enumerate(image_files)]
    
    # Test different envelope shapes
    packer = NanoFichePacker(1800, 2300)
    
    print("\n1. Testing RECTANGLE packing (aspect 1.29:1)...")
    envelope_spec = EnvelopeSpec(EnvelopeShape.RECTANGLE, 1.29, 1.0)
    result = packer.pack(len(image_bins), envelope_spec)
    print(f"   Grid: {result.rows}x{result.columns}")
    print(f"   Canvas: {result.canvas_width}x{result.canvas_height}")
    print(f"   Aspect ratio: {result.canvas_width/result.canvas_height:.3f}")
    
    print("\n2. Testing SQUARE packing...")
    envelope_spec = EnvelopeSpec(EnvelopeShape.SQUARE)
    result = packer.pack(len(image_bins), envelope_spec)
    print(f"   Grid: {result.rows}x{result.columns}")
    print(f"   Canvas: {result.canvas_width}x{result.canvas_height}")
    
    print("\n3. Testing CIRCLE packing...")
    envelope_spec = EnvelopeSpec(EnvelopeShape.CIRCLE)
    result = packer.pack(len(image_bins), envelope_spec)
    print(f"   Canvas: {result.canvas_width}x{result.canvas_height}")
    
    print("\n4. Testing ELLIPSE packing (aspect 1.5:1)...")
    envelope_spec = EnvelopeSpec(EnvelopeShape.ELLIPSE, 1.5, 1.0)
    result = packer.pack(len(image_bins), envelope_spec)
    print(f"   Canvas: {result.canvas_width}x{result.canvas_height}")
    
    # Generate a preview for the rectangle case
    print("\n5. Generating preview TIFF...")
    envelope_spec = EnvelopeSpec(EnvelopeShape.RECTANGLE, 1.29, 1.0)
    result = packer.pack(len(image_bins), envelope_spec)
    
    renderer = NanoFicheRenderer()
    preview_path = Path("test_preview.tif")
    renderer.generate_preview(image_bins, result, preview_path)
    print(f"   Preview saved to: {preview_path}")
    
    print("\nTest complete! You can now:")
    print("1. Run 'python nanofiche_image_prep.py' to use the GUI")
    print("2. Select the 'test_images' folder when prompted")
    print("3. View the generated test_preview.tif")

if __name__ == "__main__":
    test_packing()