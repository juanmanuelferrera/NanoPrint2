#!/usr/bin/env python3
"""
Test script for TRUE SPIRAL LAYOUT - starting from center, spiraling outward
Parameters: Bin size 1300x1900, TRUE SPIRAL arrangement
"""

import sys
sys.path.insert(0, '.')

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import math
import re
from nanofiche_core import ImageBin, NanoFicheRenderer
from nanofiche_core.packer import PackingResult, EnvelopeShape
from nanofiche_core.logger import setup_logging
import logging

def natural_sort_key(filename):
    """Extract numeric part for proper sorting."""
    match = re.search(r'-(\d+)\.tif$', str(filename))
    if match:
        return int(match.group(1))
    return 0

def create_true_spiral_layout(num_images, bin_width, bin_height, canvas_size):
    """Create a true spiral layout starting from center."""
    print(f"🌀 Creating true spiral layout for {num_images} images...")
    
    center_x = canvas_size // 2
    center_y = canvas_size // 2
    placements = []
    
    # Spiral parameters
    radius_increment = min(bin_width, bin_height) * 0.4  # How much radius increases per turn
    angle_increment = 0.3  # How much angle increases per step (smaller = tighter spiral)
    
    current_radius = 0
    current_angle = 0
    
    for i in range(num_images):
        # Calculate position on spiral
        x = center_x + current_radius * math.cos(current_angle) - bin_width // 2
        y = center_y + current_radius * math.sin(current_angle) - bin_height // 2
        
        # Ensure within canvas bounds
        x = max(0, min(x, canvas_size - bin_width))
        y = max(0, min(y, canvas_size - bin_height))
        
        placements.append((int(x), int(y)))
        
        # Increment spiral parameters
        current_angle += angle_increment
        current_radius += radius_increment * angle_increment / (2 * math.pi)
        
        # Debug first few and last few positions
        if i < 5 or i >= num_images - 5:
            print(f"   Image {i+1}: radius={current_radius:.1f}, angle={current_angle:.2f}, pos=({int(x)}, {int(y)})")
    
    return placements

def test_spiral_layout():
    """Test with spiral layout using subset of files."""
    setup_logging(logging.INFO)
    
    print("Testing TRUE SPIRAL LAYOUT")
    print("=" * 50)
    
    tif_folder = Path("/Users/juanmanuelferreradiaz/Downloads/tif200")
    tif_files = list(tif_folder.glob("*.tif"))
    tif_files.sort(key=natural_sort_key)
    
    # Use subset for spiral test (every 10th file for better visualization)
    test_files = tif_files[::10]  # Every 10th file
    print(f"📁 Using every 10th file: {len(test_files)} files for spiral test")
    print(f"   First: Page {natural_sort_key(test_files[0])}")
    print(f"   Last: Page {natural_sort_key(test_files[-1])}")
    
    bin_width = 1300
    bin_height = 1900
    
    # Create image bins
    image_bins = []
    for i, tif_file in enumerate(test_files):
        page_num = natural_sort_key(tif_file)
        image_bins.append(ImageBin(tif_file, bin_width, bin_height, page_num))
    
    print(f"✅ Created {len(image_bins)} image bins for spiral layout")
    
    # Calculate canvas size (square for circular spiral)
    # Estimate based on spiral area needed
    estimated_radius = math.sqrt(len(image_bins) * bin_width * bin_height / math.pi) * 1.5
    canvas_size = int(estimated_radius * 2)
    
    # Make sure it's reasonable
    canvas_size = max(canvas_size, len(image_bins) * 200)  # Minimum size
    canvas_size = min(canvas_size, 100000)  # Maximum size for memory
    
    print(f"📐 Canvas size: {canvas_size}x{canvas_size} pixels")
    
    # Create true spiral placements
    spiral_placements = create_true_spiral_layout(len(image_bins), bin_width, bin_height, canvas_size)
    
    # Create a PackingResult object for the renderer
    packing_result = PackingResult(
        rows=int(canvas_size / bin_height),
        columns=int(canvas_size / bin_width), 
        canvas_width=canvas_size,
        canvas_height=canvas_size,
        placements=spiral_placements,
        envelope_shape=EnvelopeShape.CIRCLE,
        total_bins=len(image_bins),
        bin_width=bin_width,
        bin_height=bin_height
    )
    
    # Generate visualization
    print(f"\n🖼️  Generating spiral visualization...")
    output_dir = Path("spiral_layout_output")
    output_dir.mkdir(exist_ok=True)
    
    # Create a simple visualization showing the spiral pattern
    viz_path = output_dir / "spiral_pattern_visualization.png"
    create_spiral_visualization(spiral_placements, canvas_size, bin_width, bin_height, viz_path, len(image_bins))
    
    # Generate actual thumbnail with real images
    renderer = NanoFicheRenderer()
    thumbnail_path = output_dir / "spiral_layout_thumbnail.tif"
    print(f"   Creating spiral thumbnail...")
    renderer.generate_preview(image_bins, packing_result, thumbnail_path, max_dimension=1500)
    print(f"   ✅ Spiral thumbnail saved: {thumbnail_path}")
    
    print(f"\n🌀 Spiral Layout Characteristics:")
    print(f"   Start: Center of canvas")
    print(f"   Pattern: Outward spiral (like a nautilus shell)")
    print(f"   Order: Page 1 at center, increasing outward")
    print(f"   Alignment: Follows spiral curve (not grid-aligned)")
    print(f"   Artistic: Yes! Very organic and flowing")
    
    print(f"\n📁 Output files:")
    print(f"   Spiral pattern: {viz_path.absolute()}")
    print(f"   Real images: {thumbnail_path.absolute()}")
    
    print(f"\n🎨 Artistic Potential:")
    print(f"   - Creates beautiful nautilus/galaxy-like pattern")
    print(f"   - Natural reading flow from center outward")
    print(f"   - Each 'arm' of spiral could represent chapters/sections")
    print(f"   - Very Instagram-worthy for book visualization!")
    
    return output_dir

def create_spiral_visualization(placements, canvas_size, bin_width, bin_height, output_path, num_images):
    """Create a simple visualization showing the spiral pattern."""
    
    # Create visualization image
    viz_scale = min(1200 / canvas_size, 1.0)  # Scale down for reasonable size
    viz_width = int(canvas_size * viz_scale)
    viz_height = int(canvas_size * viz_scale)
    
    img = Image.new('RGB', (viz_width, viz_height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Draw spiral path
    center_x = viz_width // 2
    center_y = viz_height // 2
    
    # Draw each page position
    for i, (x, y) in enumerate(placements):
        # Scale position
        scaled_x = int(x * viz_scale)
        scaled_y = int(y * viz_scale)
        scaled_bin_w = int(bin_width * viz_scale)
        scaled_bin_h = int(bin_height * viz_scale)
        
        # Color based on position in sequence
        hue = (i / num_images) * 360
        color = hsv_to_rgb(hue, 0.7, 0.9)
        
        # Draw rectangle for each page
        draw.rectangle([
            scaled_x, scaled_y, 
            scaled_x + scaled_bin_w, scaled_y + scaled_bin_h
        ], fill=color, outline='black', width=1)
        
        # Add page number for first few and last few
        if i < 10 or i >= num_images - 10:
            draw.text((scaled_x + 5, scaled_y + 5), str(i+1), fill='white')
    
    # Draw center point
    draw.ellipse([center_x-5, center_y-5, center_x+5, center_y+5], fill='red')
    draw.text((center_x+10, center_y-10), "START", fill='red')
    
    # Add title
    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except:
        font = ImageFont.load_default()
    
    draw.text((10, 10), f"Spiral Layout - {num_images} Images", fill='black', font=font)
    draw.text((10, 40), "Red dot = center start point", fill='red', font=font)
    
    img.save(output_path)
    print(f"   ✅ Spiral pattern visualization: {output_path}")

def hsv_to_rgb(h, s, v):
    """Convert HSV to RGB for color visualization."""
    import colorsys
    r, g, b = colorsys.hsv_to_rgb(h/360, s, v)
    return (int(r*255), int(g*255), int(b*255))

if __name__ == "__main__":
    test_spiral_layout()