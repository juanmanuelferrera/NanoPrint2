#!/usr/bin/env python3
"""
Test script for real TIFF files from /Users/juanmanuelferreradiaz/Downloads/tif200
Parameters: Bin size 1300x1900, Square shape
"""

import sys
sys.path.insert(0, '.')

from pathlib import Path
from PIL import Image
from nanofiche_core import NanoFichePacker, EnvelopeShape, EnvelopeSpec, ImageBin, NanoFicheRenderer
from nanofiche_core.logger import setup_logging
import logging

def analyze_real_tifs():
    """Analyze the actual TIFF files in the Downloads folder."""
    tif_folder = Path("/Users/juanmanuelferreradiaz/Downloads/tif200")
    
    if not tif_folder.exists():
        print(f"❌ Folder not found: {tif_folder}")
        return None
    
    # Get all TIFF files
    tif_files = list(tif_folder.glob("*.tif"))
    tif_files.sort()  # Sort by filename
    
    print(f"📁 Found {len(tif_files)} TIFF files")
    
    # Check dimensions of first few files
    print(f"\n🔍 Checking dimensions of sample files...")
    sample_files = tif_files[:5] + tif_files[-5:]  # First 5 and last 5
    
    dimensions = []
    for i, tif_file in enumerate(sample_files):
        try:
            with Image.open(tif_file) as img:
                width, height = img.size
                dimensions.append((width, height))
                if i < 5:
                    print(f"   {tif_file.name}: {width} x {height}")
                else:
                    print(f"   {tif_file.name}: {width} x {height}")
        except Exception as e:
            print(f"   ❌ Error reading {tif_file.name}: {e}")
    
    # Check if dimensions are consistent
    if dimensions:
        unique_dims = set(dimensions)
        if len(unique_dims) == 1:
            print(f"✅ All sample files have consistent dimensions: {dimensions[0][0]} x {dimensions[0][1]}")
            return tif_files, dimensions[0]
        else:
            print(f"⚠️  Multiple dimensions found: {unique_dims}")
            return tif_files, dimensions[0]  # Use first one
    
    return None, None

def test_with_real_tifs():
    """Test with the actual TIFF files using specified parameters."""
    setup_logging(logging.INFO)
    
    print("Testing NanoFiche with Real TIFF Files")
    print("=" * 60)
    
    # Analyze the real files
    tif_files, actual_dims = analyze_real_tifs()
    if not tif_files:
        return
    
    actual_width, actual_height = actual_dims
    print(f"\n📋 Test Parameters:")
    print(f"   Actual image size: {actual_width} x {actual_height} pixels")
    print(f"   Bin size: 1300 x 1900 pixels")
    print(f"   Envelope shape: Square")
    print(f"   Total files: {len(tif_files)}")
    
    # Check if images fit in bins
    bin_width = 1300
    bin_height = 1900
    
    if actual_width <= bin_width and actual_height <= bin_height:
        print(f"✅ Images fit within bins")
        print(f"   Horizontal padding: {(bin_width - actual_width) / 2:.1f} pixels each side")
        print(f"   Vertical padding: {(bin_height - actual_height) / 2:.1f} pixels each side")
    else:
        print(f"❌ Images DO NOT fit within bins!")
        print(f"   Image exceeds bin by: {max(0, actual_width - bin_width)} x {max(0, actual_height - bin_height)}")
        return
    
    # Create ImageBin objects (use first 100 files for testing)
    print(f"\n🔄 Processing first 100 files for testing...")
    test_files = tif_files[:100]
    image_bins = []
    
    for i, tif_file in enumerate(test_files):
        try:
            # Verify the file can be opened
            with Image.open(tif_file) as img:
                width, height = img.size
                if width <= bin_width and height <= bin_height:
                    image_bins.append(ImageBin(tif_file, bin_width, bin_height, i))
                else:
                    print(f"   Skipping oversized file: {tif_file.name} ({width}x{height})")
        except Exception as e:
            print(f"   Skipping unreadable file: {tif_file.name} - {e}")
    
    print(f"✅ Created {len(image_bins)} valid image bins")
    
    # Test square packing
    print(f"\n📦 Calculating optimal square packing...")
    packer = NanoFichePacker(bin_width, bin_height)
    envelope_spec = EnvelopeSpec(EnvelopeShape.SQUARE)
    result = packer.pack(len(image_bins), envelope_spec)
    
    print(f"\n📊 Packing Results:")
    print(f"   Grid: {result.rows} rows x {result.columns} columns")
    print(f"   Canvas size: {result.canvas_width:,} x {result.canvas_height:,} pixels")
    print(f"   Total area: {result.canvas_width * result.canvas_height:,} pixels")
    print(f"   Bins packed: {len(image_bins)}")
    
    # Generate preview/thumbnail
    print(f"\n🖼️  Generating preview TIFF...")
    output_dir = Path("real_tif_test_output")
    output_dir.mkdir(exist_ok=True)
    
    renderer = NanoFicheRenderer()
    
    # Generate small thumbnail for easy viewing
    thumbnail_path = output_dir / "real_tifs_square_thumbnail.tif"
    renderer.generate_preview(image_bins, result, thumbnail_path, max_dimension=1000)
    print(f"   Thumbnail saved: {thumbnail_path}")
    
    # Generate larger preview
    preview_path = output_dir / "real_tifs_square_preview.tif"
    renderer.generate_preview(image_bins, result, preview_path, max_dimension=4000)
    print(f"   Preview saved: {preview_path}")
    
    # Generate log
    from nanofiche_core.logger import log_project
    from datetime import datetime
    
    log_path = output_dir / "real_tifs_test.log"
    log_project(
        log_path=log_path,
        project_name="real_tifs_square_test",
        timestamp=datetime.now(),
        bin_width=bin_width,
        bin_height=bin_height,
        envelope_shape="square",
        num_files=len(image_bins),
        output_path=preview_path,
        final_size=(result.canvas_width, result.canvas_height),
        process_time=2.0,
        approved=False,
        images_placed=len(image_bins)
    )
    print(f"   Log saved: {log_path}")
    
    print(f"\n✅ Test completed successfully!")
    print(f"\n📁 Output files:")
    print(f"   Thumbnail (1000px): {thumbnail_path.absolute()}")
    print(f"   Preview (4000px): {preview_path.absolute()}")
    print(f"   Log file: {log_path.absolute()}")
    
    print(f"\n💡 To test with all {len(tif_files)} files:")
    print(f"   1. Run the GUI: python nanofiche_image_prep.py")
    print(f"   2. Set bin size: 1300 x 1900")
    print(f"   3. Select folder: /Users/juanmanuelferreradiaz/Downloads/tif200")
    print(f"   4. Choose shape: Square")

if __name__ == "__main__":
    test_with_real_tifs()