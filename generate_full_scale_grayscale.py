#!/usr/bin/env python3
"""
Generate FULL SCALE 8-bit GRAYSCALE TIFF - Final production version
- Color thumbnails for preview
- 8-bit grayscale for full scale (66% memory savings)
- Automatic generation without prompts
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

def generate_full_scale():
    """Generate both color preview and grayscale full-scale TIFF."""
    setup_logging(logging.INFO)
    
    print("NANOFICHE IMAGE PREP - FINAL PRODUCTION RUN")
    print("=" * 60)
    
    tif_folder = Path("/Users/juanmanuelferreradiaz/Downloads/tif200")
    tif_files = list(tif_folder.glob("*.tif"))
    tif_files.sort(key=natural_sort_key)
    
    print(f"📁 Processing ALL {len(tif_files)} TIFF files")
    print(f"📋 Final Production Parameters:")
    print(f"   Bin size: 1300 x 1900 pixels")
    print(f"   Envelope shape: Square")
    print(f"   Preview: Color (RGB)")
    print(f"   Full scale: 8-bit grayscale")
    print(f"   Compression: LZW")
    print(f"   DPI: 300")
    
    # Process all files
    bin_width = 1300
    bin_height = 1900
    image_bins = []
    
    print(f"\n🔄 Processing files in numeric order...")
    
    for i, tif_file in enumerate(tif_files):
        if i % 100 == 0:
            print(f"   File {i+1}/{len(tif_files)}: {tif_file.name}")
        
        try:
            with Image.open(tif_file) as img:
                width, height = img.size
                if width <= bin_width and height <= bin_height:
                    page_num = natural_sort_key(tif_file)
                    image_bins.append(ImageBin(tif_file, bin_width, bin_height, page_num))
        except Exception as e:
            print(f"   ❌ Error reading {tif_file.name}: {e}")
    
    print(f"✅ Processed {len(image_bins)} valid images")
    print(f"   First: Page {image_bins[0].index}")
    print(f"   Last: Page {image_bins[-1].index}")
    
    # Calculate packing
    print(f"\n📦 Calculating optimal square packing...")
    packer = NanoFichePacker(bin_width, bin_height)
    envelope_spec = EnvelopeSpec(EnvelopeShape.SQUARE)
    result = packer.pack(len(image_bins), envelope_spec)
    
    # Memory calculations
    total_pixels = result.canvas_width * result.canvas_height
    grayscale_memory_gb = (total_pixels * 1) / (1024**3)
    rgb_memory_gb = (total_pixels * 3) / (1024**3)
    
    print(f"\n📊 Final Layout:")
    print(f"   Grid: {result.rows}×{result.columns}")
    print(f"   Canvas: {result.canvas_width:,}×{result.canvas_height:,} pixels")
    print(f"   Total: {total_pixels:,} pixels ({total_pixels/1_000_000:.1f} megapixels)")
    print(f"   Memory (grayscale): {grayscale_memory_gb:.2f} GB")
    print(f"   Memory savings vs RGB: {((rgb_memory_gb - grayscale_memory_gb)/rgb_memory_gb)*100:.1f}%")
    
    # Create output directory
    output_dir = Path("nanofiche_final_output")
    output_dir.mkdir(exist_ok=True)
    
    renderer = NanoFicheRenderer()
    
    # Step 1: Generate COLOR preview
    print(f"\n🎨 Step 1: Generating COLOR preview...")
    preview_path = output_dir / "nanofiche_color_preview.tif"
    renderer.generate_preview(image_bins, result, preview_path, max_dimension=4000, color=True)
    preview_size_mb = preview_path.stat().st_size / (1024**2)
    print(f"   ✅ Color preview: {preview_path} ({preview_size_mb:.1f} MB)")
    
    # Step 2: Generate GRAYSCALE full scale
    print(f"\n⚫ Step 2: Generating GRAYSCALE full scale...")
    print(f"   ⚠️  This will create a {grayscale_memory_gb:.2f} GB file and may take 10-30 minutes")
    
    full_path = output_dir / "nanofiche_full_scale_grayscale.tif"
    log_path = output_dir / "nanofiche_production.log"
    
    try:
        print(f"   🚀 Starting full scale generation...")
        renderer.generate_full_tiff(
            image_bins, 
            result, 
            full_path, 
            log_path, 
            "nanofiche_production", 
            approved=True,
            grayscale=True
        )
        
        # Check final file size
        full_size_mb = full_path.stat().st_size / (1024**2)
        full_size_gb = full_size_mb / 1024
        
        print(f"   ✅ Full scale TIFF completed!")
        print(f"   📁 File: {full_path}")
        print(f"   📏 Size: {full_size_gb:.2f} GB ({full_size_mb:.0f} MB)")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return
    
    # Summary
    print(f"\n🎯 PRODUCTION COMPLETE!")
    print(f"=" * 40)
    print(f"📁 Output Files:")
    print(f"   Color Preview: {preview_path.name} ({preview_size_mb:.1f} MB)")
    print(f"   Full Scale: {full_path.name} ({full_size_gb:.2f} GB)")
    print(f"   Log File: {log_path.name}")
    print(f"")
    print(f"📊 Statistics:")
    print(f"   Images processed: {len(image_bins)}")
    print(f"   Final canvas: {result.canvas_width:,}×{result.canvas_height:,}")
    print(f"   Memory savings: 66.7% (grayscale vs RGB)")
    print(f"   Format: 8-bit grayscale TIFF with LZW compression")
    print(f"")
    print(f"📂 All files saved to: {output_dir.absolute()}")

if __name__ == "__main__":
    generate_full_scale()