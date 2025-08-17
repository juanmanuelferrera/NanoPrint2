#!/usr/bin/env python3
"""
Test script for ALL 1034 TIFF files - CIRCLE envelope with PROPER NUMERIC ORDER
Parameters: Bin size 1300x1900, CIRCLE shape, files sorted numerically by page number
"""

import sys
sys.path.insert(0, '.')

from pathlib import Path
from PIL import Image
import re
from nanofiche_core import NanoFichePacker, EnvelopeShape, EnvelopeSpec, ImageBin, NanoFicheRenderer
from nanofiche_core.logger import setup_logging
import logging

def natural_sort_key(filename):
    """Extract numeric part for proper sorting (1, 2, 3... 10, 11... 100, 101...)"""
    # Extract the number from filename like "...-123.tif"
    match = re.search(r'-(\d+)\.tif$', str(filename))
    if match:
        return int(match.group(1))
    return 0

def test_circle_numeric_order():
    """Test with ALL 1034 TIFF files using CIRCLE envelope with proper numeric order."""
    setup_logging(logging.INFO)
    
    print("Testing NanoFiche - CIRCLE with NUMERIC ORDER")
    print("=" * 60)
    
    tif_folder = Path("/Users/juanmanuelferreradiaz/Downloads/tif200")
    tif_files = list(tif_folder.glob("*.tif"))
    
    # Sort files by numeric order instead of alphabetical
    print(f"📁 Sorting {len(tif_files)} files by numeric order...")
    tif_files.sort(key=natural_sort_key)
    
    # Show first and last few files to verify order
    print(f"   First 5 files:")
    for i in range(min(5, len(tif_files))):
        page_num = natural_sort_key(tif_files[i])
        print(f"     Page {page_num}: {tif_files[i].name}")
    
    print(f"   Last 5 files:")
    for i in range(max(0, len(tif_files)-5), len(tif_files)):
        page_num = natural_sort_key(tif_files[i])
        print(f"     Page {page_num}: {tif_files[i].name}")
    
    print(f"📋 Parameters:")
    print(f"   Bin size: 1300 x 1900 pixels")
    print(f"   Envelope shape: CIRCLE")
    print(f"   Sorting: Numeric by page number")
    
    # Create ImageBin objects for ALL files in numeric order
    bin_width = 1300
    bin_height = 1900
    image_bins = []
    oversized_files = []
    
    print(f"\n🔄 Processing files in numeric order...")
    
    for i, tif_file in enumerate(tif_files):
        if i % 100 == 0:
            print(f"   Processing file {i+1}/{len(tif_files)}...")
        
        try:
            with Image.open(tif_file) as img:
                width, height = img.size
                if width <= bin_width and height <= bin_height:
                    # Use the actual page number as index for better tracking
                    page_num = natural_sort_key(tif_file)
                    image_bins.append(ImageBin(tif_file, bin_width, bin_height, page_num))
                else:
                    oversized_files.append(f"{tif_file.name} ({width}x{height})")
        except Exception as e:
            print(f"   ❌ Error reading {tif_file.name}: {e}")
    
    print(f"✅ Created {len(image_bins)} valid image bins in numeric order")
    print(f"   First image: Page {image_bins[0].index} ({image_bins[0].file_path.name})")
    print(f"   Last image: Page {image_bins[-1].index} ({image_bins[-1].file_path.name})")
    
    # Calculate optimal CIRCLE packing
    print(f"\n🔵 Calculating CIRCLE packing with grid-based arrangement...")
    packer = NanoFichePacker(bin_width, bin_height)
    envelope_spec = EnvelopeSpec(EnvelopeShape.CIRCLE)
    result = packer.pack(len(image_bins), envelope_spec)
    
    print(f"\n📊 CIRCLE Packing Results:")
    print(f"   Canvas size: {result.canvas_width:,} x {result.canvas_height:,} pixels")
    print(f"   Circle diameter: {result.canvas_width:,} pixels")
    print(f"   Total area: {result.canvas_width * result.canvas_height:,} pixels")
    print(f"   Bins packed: {len(image_bins)}")
    
    # Generate thumbnail with enhanced debugging
    print(f"\n🖼️  Generating CIRCLE thumbnail with numeric order...")
    output_dir = Path("circle_numeric_order_output")
    output_dir.mkdir(exist_ok=True)
    
    renderer = NanoFicheRenderer()
    
    # Generate thumbnail
    thumbnail_path = output_dir / "circle_numeric_order_thumbnail.tif"
    print(f"   Creating thumbnail...")
    renderer.generate_preview(image_bins, result, thumbnail_path, max_dimension=1200)
    print(f"   ✅ Thumbnail saved: {thumbnail_path}")
    
    # Debug: Show where specific pages are placed
    print(f"\n🔍 Checking placement of key pages:")
    key_pages = [1, 2, 3, len(image_bins)-2, len(image_bins)-1, len(image_bins)]
    
    for page_idx in key_pages:
        if page_idx <= len(image_bins) and page_idx > 0:
            array_idx = page_idx - 1  # Convert to 0-based index
            if array_idx < len(result.placements):
                x, y = result.placements[array_idx]
                page_num = image_bins[array_idx].index
                filename = image_bins[array_idx].file_path.name
                print(f"   Page {page_num} ({filename}): position ({x}, {y})")
    
    # Generate log
    from nanofiche_core.logger import log_project
    from datetime import datetime
    
    log_path = output_dir / "circle_numeric_order_test.log"
    log_project(
        log_path=log_path,
        project_name="circle_numeric_order_test",
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
    
    print(f"\n🎯 Results with Numeric Order:")
    print(f"   Files are now sorted: 1, 2, 3... 1034 (not 1, 10, 100...)")
    print(f"   Circle arrangement: Grid-based placement within circle")
    print(f"   Last page should now be in proper position")
    
    print(f"\n📁 Output files:")
    print(f"   Thumbnail: {thumbnail_path.absolute()}")
    print(f"   Log: {log_path.absolute()}")
    
    print(f"\n✅ CIRCLE test with numeric order completed!")

if __name__ == "__main__":
    test_circle_numeric_order()