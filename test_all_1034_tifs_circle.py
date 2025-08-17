#!/usr/bin/env python3
"""
Test script for ALL 1034 TIFF files - CIRCLE envelope
Parameters: Bin size 1300x1900, CIRCLE shape
"""

import sys
sys.path.insert(0, '.')

from pathlib import Path
from PIL import Image
from nanofiche_core import NanoFichePacker, EnvelopeShape, EnvelopeSpec, ImageBin, NanoFicheRenderer
from nanofiche_core.logger import setup_logging
import logging

def test_all_1034_files_circle():
    """Test with ALL 1034 TIFF files using CIRCLE envelope."""
    setup_logging(logging.INFO)
    
    print("Testing NanoFiche with ALL 1034 TIFF Files - CIRCLE")
    print("=" * 60)
    
    tif_folder = Path("/Users/juanmanuelferreradiaz/Downloads/tif200")
    tif_files = list(tif_folder.glob("*.tif"))
    tif_files.sort()
    
    print(f"📁 Processing all {len(tif_files)} TIFF files")
    print(f"📋 Parameters:")
    print(f"   Bin size: 1300 x 1900 pixels")
    print(f"   Envelope shape: CIRCLE")
    
    # Create ImageBin objects for ALL files
    bin_width = 1300
    bin_height = 1900
    image_bins = []
    oversized_files = []
    
    print(f"\n🔄 Validating all {len(tif_files)} files...")
    
    for i, tif_file in enumerate(tif_files):
        if i % 100 == 0:
            print(f"   Processing file {i+1}/{len(tif_files)}...")
        
        try:
            with Image.open(tif_file) as img:
                width, height = img.size
                if width <= bin_width and height <= bin_height:
                    image_bins.append(ImageBin(tif_file, bin_width, bin_height, i))
                else:
                    oversized_files.append(f"{tif_file.name} ({width}x{height})")
        except Exception as e:
            print(f"   ❌ Error reading {tif_file.name}: {e}")
    
    if oversized_files:
        print(f"⚠️  Found {len(oversized_files)} oversized files:")
        for f in oversized_files[:5]:  # Show first 5
            print(f"     {f}")
        if len(oversized_files) > 5:
            print(f"     ... and {len(oversized_files) - 5} more")
    
    print(f"✅ Created {len(image_bins)} valid image bins")
    
    # Calculate optimal CIRCLE packing for ALL files
    print(f"\n🔵 Calculating optimal CIRCLE packing for {len(image_bins)} images...")
    packer = NanoFichePacker(bin_width, bin_height)
    envelope_spec = EnvelopeSpec(EnvelopeShape.CIRCLE)
    result = packer.pack(len(image_bins), envelope_spec)
    
    print(f"\n📊 Final CIRCLE Packing Results:")
    print(f"   Canvas size: {result.canvas_width:,} x {result.canvas_height:,} pixels")
    print(f"   Circle diameter: {result.canvas_width:,} pixels")
    print(f"   Total area: {result.canvas_width * result.canvas_height:,} pixels")
    print(f"   Bins packed: {len(image_bins)}")
    print(f"   Canvas area in megapixels: {(result.canvas_width * result.canvas_height) / 1_000_000:.1f} MP")
    
    # Calculate circle area vs square area
    import math
    radius = result.canvas_width / 2
    circle_area = math.pi * radius * radius
    square_area = result.canvas_width * result.canvas_height
    circle_efficiency = (circle_area / square_area) * 100
    
    print(f"   Circle area: {circle_area:,.0f} pixels ({circle_efficiency:.1f}% of bounding square)")
    
    # Estimate memory usage
    bytes_per_pixel = 3  # RGB
    total_bytes = result.canvas_width * result.canvas_height * bytes_per_pixel
    gb_needed = total_bytes / (1024**3)
    print(f"   Estimated memory needed: {gb_needed:.2f} GB")
    
    # Generate thumbnail
    print(f"\n🖼️  Generating CIRCLE thumbnail preview...")
    output_dir = Path("all_1034_circle_test_output")
    output_dir.mkdir(exist_ok=True)
    
    renderer = NanoFicheRenderer()
    
    # Generate small thumbnail for viewing the circular layout
    thumbnail_path = output_dir / "all_1034_tifs_circle_thumbnail.tif"
    print(f"   Creating circular thumbnail (this may take a few minutes)...")
    renderer.generate_preview(image_bins, result, thumbnail_path, max_dimension=1200)
    print(f"   ✅ Thumbnail saved: {thumbnail_path}")
    
    # Generate log
    from nanofiche_core.logger import log_project
    from datetime import datetime
    
    log_path = output_dir / "all_1034_tifs_circle_test.log"
    log_project(
        log_path=log_path,
        project_name="all_1034_tifs_circle_test",
        timestamp=datetime.now(),
        bin_width=bin_width,
        bin_height=bin_height,
        envelope_shape="circle",
        num_files=len(image_bins),
        output_path=thumbnail_path,
        final_size=(result.canvas_width, result.canvas_height),
        process_time=5.0,
        approved=False,
        images_placed=len(image_bins)
    )
    print(f"   ✅ Log saved: {log_path}")
    
    print(f"\n🎯 CIRCLE Test Results Summary:")
    print(f"   Total files processed: {len(tif_files)}")
    print(f"   Valid files packed: {len(image_bins)}")
    print(f"   Circle diameter: {result.canvas_width:,} pixels")
    print(f"   Final canvas: {result.canvas_width:,}×{result.canvas_height:,} pixels")
    print(f"   Packing pattern: Spiral arrangement")
    
    print(f"\n📁 Output files:")
    print(f"   Thumbnail: {thumbnail_path.absolute()}")
    print(f"   Log: {log_path.absolute()}")
    
    print(f"\n🔵 Circle vs Square Comparison:")
    print(f"   Circle uses {circle_efficiency:.1f}% of the bounding square area")
    print(f"   More organic, spiral layout vs rigid grid")
    
    print(f"\n✅ CIRCLE test completed! You can now view the circular layout thumbnail.")

if __name__ == "__main__":
    test_all_1034_files_circle()