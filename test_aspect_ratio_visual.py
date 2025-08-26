#!/usr/bin/env python3
"""Visual test of aspect ratio fix with preview generation."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from pathlib import Path
from nanofiche_core.packer import NanoFichePacker, EnvelopeSpec, EnvelopeShape
from nanofiche_core.renderer import NanoFicheRenderer
from nanofiche_core.image_bin import ImageBin
from nanofiche_core.logger import setup_logging
from PIL import Image
import glob

def test_aspect_ratio_visual():
    """Test aspect ratio fix and generate visual preview."""
    setup_logging()
    
    # Use subset for testing
    dataset_path = Path("/Users/juanmanuelferreradiaz/Downloads/tif200")
    if not dataset_path.exists():
        print("Dataset not found! Need /Users/juanmanuelferreradiaz/Downloads/tif200")
        return
        
    image_files = sorted(glob.glob(str(dataset_path / "*.tif")))[:200]  # Medium test
    print(f"ASPECT RATIO VISUAL TEST - {len(image_files)} TIF images")
    print("=" * 60)
    
    # Create image bins
    image_bins = []
    for f in image_files:
        with Image.open(f) as img:
            image_bins.append(ImageBin(file_path=Path(f), width=img.width, height=img.height))
    
    packer = NanoFichePacker(bin_width=1300, bin_height=1900)
    
    # Test with custom wide aspect ratio (3:1 - very wide reserve)
    print(f"\n🎨 Testing Wide Reserve Aspect Ratio (3:1)")
    print("-" * 50)
    
    spec = EnvelopeSpec(
        shape=EnvelopeShape.SQUARE,
        reserve_enabled=True,
        reserve_width=5000,
        reserve_height=5000,
        reserve_position="top-left",
        reserve_auto_size=True,
        reserve_aspect_x=3.0,  # Very wide reserve
        reserve_aspect_y=1.0
    )
    
    result = packer.pack(len(image_bins), spec)
    reserve_aspect = spec.reserve_width / spec.reserve_height
    target_aspect = 3.0 / 1.0
    
    print(f"Canvas: {result.canvas_width}x{result.canvas_height}")
    print(f"Reserve: {spec.reserve_width}x{spec.reserve_height}")
    print(f"Reserve aspect ratio: {reserve_aspect:.3f}")
    print(f"Target aspect ratio: {target_aspect:.3f}")
    print(f"Images placed: {len(result.placements)}")
    
    # Calculate efficiency
    image_area = len(image_bins) * 1300 * 1900
    total_area = result.canvas_width * result.canvas_height
    efficiency = (image_area / total_area) * 100
    
    print(f"Efficiency: {efficiency:.1f}%")
    
    # Generate preview
    print(f"\n🖼️  Generating Visual Preview")
    print("-" * 50)
    
    renderer = NanoFicheRenderer()
    preview_path = Path("aspect_ratio_test_preview.tif")
    
    renderer.generate_preview(
        image_bins=image_bins,
        packing_result=result,
        output_path=preview_path,
        max_dimension=1500,  # Good size for viewing
        color=True
    )
    
    print(f"Preview saved to: {preview_path}")
    print(f"Shows: {len(image_bins)} images with {spec.reserve_width}x{spec.reserve_height} wide red rectangle (3:1 ratio)")
    print(f"Reserve position: top-left corner")
    
    return result, preview_path

if __name__ == "__main__":
    result, preview_path = test_aspect_ratio_visual()
    
    # Copy to clipboard
    import subprocess
    abs_path = os.path.abspath(preview_path)
    subprocess.run(['osascript', '-e', f'set the clipboard to (read (POSIX file "{abs_path}") as TIFF picture)'])
    print(f"\n📋 Preview copied to clipboard!")
    print(f"You can now paste the image to see the wide (3:1) reserve space aspect ratio in action.")