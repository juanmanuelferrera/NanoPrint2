#!/usr/bin/env python3
"""
Test script for FULL SCALE 8-bit GRAYSCALE TIFF generation
Parameters: ALL 1034 files, Bin size 1300x1900, Square shape, 8-bit grayscale
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
    """Extract numeric part for proper sorting."""
    match = re.search(r'-(\d+)\.tif$', str(filename))
    if match:
        return int(match.group(1))
    return 0

def test_full_scale_grayscale():
    """Test full scale grayscale TIFF generation."""
    setup_logging(logging.INFO)
    
    print("Testing FULL SCALE 8-BIT GRAYSCALE TIFF")
    print("=" * 60)
    
    tif_folder = Path("/Users/juanmanuelferreradiaz/Downloads/tif200")
    tif_files = list(tif_folder.glob("*.tif"))
    tif_files.sort(key=natural_sort_key)
    
    print(f"📁 Processing ALL {len(tif_files)} TIFF files")
    print(f"📋 Parameters:")
    print(f"   Bin size: 1300 x 1900 pixels")
    print(f"   Envelope shape: Square")
    print(f"   Output format: 8-bit grayscale TIFF")
    print(f"   Compression: LZW")
    
    # Create ImageBin objects for ALL files
    bin_width = 1300
    bin_height = 1900
    image_bins = []
    
    print(f"\n🔄 Validating all files...")
    
    for i, tif_file in enumerate(tif_files):
        if i % 100 == 0:
            print(f"   Processing file {i+1}/{len(tif_files)}...")
        
        try:
            with Image.open(tif_file) as img:
                width, height = img.size
                if width <= bin_width and height <= bin_height:
                    page_num = natural_sort_key(tif_file)
                    image_bins.append(ImageBin(tif_file, bin_width, bin_height, page_num))
        except Exception as e:
            print(f"   ❌ Error reading {tif_file.name}: {e}")
    
    print(f"✅ Created {len(image_bins)} valid image bins")
    
    # Calculate optimal square packing
    print(f"\n📦 Calculating optimal square packing...")
    packer = NanoFichePacker(bin_width, bin_height)
    envelope_spec = EnvelopeSpec(EnvelopeShape.SQUARE)
    result = packer.pack(len(image_bins), envelope_spec)
    
    # Calculate memory usage for both RGB and grayscale
    total_pixels = result.canvas_width * result.canvas_height
    rgb_memory_gb = (total_pixels * 3) / (1024**3)
    grayscale_memory_gb = (total_pixels * 1) / (1024**3)
    memory_savings = ((rgb_memory_gb - grayscale_memory_gb) / rgb_memory_gb) * 100
    
    print(f"\n📊 Final Results:")
    print(f"   Grid: {result.rows} rows x {result.columns} columns")
    print(f"   Canvas size: {result.canvas_width:,} x {result.canvas_height:,} pixels")
    print(f"   Total pixels: {total_pixels:,}")
    print(f"   Memory usage (RGB): {rgb_memory_gb:.2f} GB")
    print(f"   Memory usage (Grayscale): {grayscale_memory_gb:.2f} GB")
    print(f"   Memory savings: {memory_savings:.1f}%")
    
    # Generate outputs
    print(f"\n🖼️  Generating outputs...")
    output_dir = Path("full_scale_grayscale_output")
    output_dir.mkdir(exist_ok=True)
    
    renderer = NanoFicheRenderer()
    
    # Generate small preview first (to verify layout)
    preview_path = output_dir / "full_scale_preview.tif"
    print(f"   Creating preview (4000px max)...")
    renderer.generate_preview(image_bins, result, preview_path, max_dimension=4000)
    print(f"   ✅ Preview saved: {preview_path}")
    
    # Ask user before generating massive full-scale file
    print(f"\n⚠️  WARNING: Full scale generation will create a {grayscale_memory_gb:.2f} GB file!")
    print(f"   Canvas: {result.canvas_width:,} x {result.canvas_height:,} pixels")
    print(f"   This may take 10-30 minutes and require significant memory.")
    
    response = input(f"\n🤔 Generate full scale grayscale TIFF? (y/N): ").lower().strip()
    
    if response == 'y' or response == 'yes':
        # Generate full scale grayscale TIFF
        full_path = output_dir / "full_scale_grayscale.tif"
        log_path = output_dir / "full_scale_grayscale.log"
        
        print(f"\n🚀 Generating full scale 8-bit grayscale TIFF...")
        print(f"   This may take a while - processing {len(image_bins)} images...")
        
        try:
            renderer.generate_full_tiff(
                image_bins, 
                result, 
                full_path, 
                log_path, 
                "full_scale_grayscale", 
                approved=True,
                grayscale=True  # Enable grayscale mode
            )
            print(f"   ✅ Full scale TIFF completed: {full_path}")
            print(f"   ✅ Log saved: {log_path}")
            
            # Check file size
            file_size_mb = full_path.stat().st_size / (1024**2)
            print(f"   📁 File size: {file_size_mb:.1f} MB")
            
        except Exception as e:
            print(f"   ❌ Error generating full TIFF: {e}")
            
    else:
        print(f"\n⏭️  Skipped full scale generation.")
    
    print(f"\n📁 Output files:")
    print(f"   Preview: {preview_path.absolute()}")
    if response == 'y' or response == 'yes':
        print(f"   Full scale: {output_dir / 'full_scale_grayscale.tif'}")
        print(f"   Log: {output_dir / 'full_scale_grayscale.log'}")
    
    print(f"\n✅ Grayscale test completed!")
    print(f"\n💡 Benefits of 8-bit grayscale:")
    print(f"   - 66% less memory usage ({grayscale_memory_gb:.2f} GB vs {rgb_memory_gb:.2f} GB)")
    print(f"   - Faster processing and file operations")
    print(f"   - Smaller file sizes")
    print(f"   - Perfect for text/document scanning applications")

if __name__ == "__main__":
    test_full_scale_grayscale()