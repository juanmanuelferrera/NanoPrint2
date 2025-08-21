# NanoFiche Image Prep

Windows application for optimal bin packing of raster images into various envelope shapes.

![Build Status](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/build-exe.yml/badge.svg)

## 🚀 Quick Start

### Download Pre-built EXE
1. Go to [Releases](https://github.com/YOUR_USERNAME/YOUR_REPO/releases)
2. Download `NanoFiche_Image_Prep.exe`
3. Run - no installation required!

## 📋 Features

- **Optimal Bin Packing**: Efficiently arrange fixed-size image bins into envelope shapes
- **Multiple Envelope Shapes**: 
  - Square
  - Rectangle (with custom aspect ratio)
  - Circle
  - Ellipse (with custom aspect ratio)
- **Advanced Reserved Spaces**: 
  - Fixed pixel-based reserves (e.g., 5000×5000 center square)
  - Percentage-based shaped reserves (circle, square, rectangle)
  - Dual exclusion zones (corner + center combinations)
- **Smart Validation**: Automatic checking of image dimensions against bin limits
- **Preview System**: Generate downsampled preview (max 4000px) before final rendering
- **Approval Workflow**: Review layouts before generating full resolution TIFF
- **Comprehensive Logging**: Detailed project logs with all parameters and results
- **8-bit Grayscale Output**: Memory-efficient full-scale generation (66% less memory than RGB)
- **Color Previews**: Thumbnails and previews remain in color for better visualization
- **Bottom Row Optimization**: Algorithms to maximize bottom row utilization
- **Top-Left Priority Placement**: Sequential placement from top-left to bottom-right

## 🛠️ Building from Source

### Requirements
- Python 3.8+
- pip

### Setup
```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run application
python nanofiche_image_prep.py
```

### Build EXE locally
```bash
pyinstaller nanofiche_image_prep.spec
# EXE will be in dist/ folder
```

## 📖 Usage Guide

1. **Project Setup**
   - Enter project name
   - Set bin dimensions (width × height in pixels)
   
2. **Choose Envelope Shape**
   - Square: Equal dimensions
   - Rectangle: Specify aspect ratio (e.g., 1.29:1)
   - Circle: Circular packing
   - Ellipse: Specify aspect ratio

3. **Select Files**
   - Browse to folder with raster images
   - Choose output location

4. **Validate & Preview**
   - Click "Validate & Calculate"
   - Generate preview TIFF
   - Review the layout

5. **Final Output**
   - Approve → Full resolution TIFF
   - Reject → Thumbnail only

## 📁 Output Files

- `[project]_[timestamp]_full.tif` - Full resolution output (8-bit grayscale for memory efficiency)
- `[project]_[timestamp]_thumbnail.tif` - Reduced size (rejected layouts, color)
- `[project]_[timestamp]_[full|thumbnail].log` - Detailed project log

### Output Formats
- **Full Scale**: 8-bit grayscale TIFF with LZW compression at 300 DPI
- **Previews/Thumbnails**: Color RGB TIFF with LZW compression at 200 DPI
- **Memory Savings**: Grayscale uses 66% less memory than RGB (1 byte vs 3 bytes per pixel)

## 🔧 Supported Formats

- PNG
- JPG/JPEG
- TIFF/TIF
- BMP

## 📊 Algorithm Details

The application implements sophisticated packing algorithms:

### Core Packing Algorithms
- **Rectangle Packing**: Optimizes grid layout to match target aspect ratio while minimizing area
- **Circle/Ellipse**: Uses spiral placement for optimal space utilization
- **Binary Search Optimization**: Automatically finds optimal envelope dimensions for maximum efficiency
- **Numeric Ordering**: Files are sorted by numeric suffix for proper page sequence
- All algorithms maintain original image aspect ratios within bins

### Advanced Reserve Space Features
- **Fixed Pixel Reserves**: Exact pixel dimensions (e.g., 5000×5000 center square)
- **Percentage-based Reserves**: Sized as percentage of envelope width (10%, 15%, 20%)
- **Shaped Exclusion Zones**: Circle, square, and rectangle reserves at center
- **Dual Exclusion**: Combination of corner reserves + center shapes
- **Top-Left Priority**: Sequential placement from (0,0) ensuring first page at top-left
- **Bottom Row Optimization**: Algorithms to achieve 100% bottom row utilization

### Placement Strategies
- **Pixel-Perfect Geometry**: Reserves calculated in exact pixel dimensions for precision
- **Collision Detection**: Tile-level checking against shaped exclusion zones
- **Optimal Envelope Sizing**: Binary search to find most efficient rectangle dimensions
- **Visual Preview Generation**: Red overlay highlighting for exact reserve visualization

### Performance Optimizations
- **8-bit Grayscale**: Reduces memory usage by 66% compared to RGB
- **LZW Compression**: Efficient TIFF compression for smaller file sizes
- **Progressive Processing**: Large datasets processed in batches to manage memory
- **Efficient Algorithms**: Achieve 90-97% packing efficiency with optimized placement

## 🧪 Test Suite

The repository includes comprehensive test algorithms for advanced packing scenarios:

### Reserve Space Tests
- `test_fixed_5000_reserve.py` - Fixed 5000×5000 pixel center square
- `test_shaped_reserve.py` - Percentage-based shaped reserves (circle, square, rectangle)
- `test_rectangle_with_expanded_reserve.py` - Rectangle with optimized reserve spaces
- `test_square_with_expanded_reserve.py` - Square with expandable corner reserves

### Optimization Tests  
- `test_compare_bottom_filling.py` - Bottom row utilization comparison
- `test_optimized_6x6_reserve.py` - 6×6 vs 4×4 reserve size optimization
- `test_binary_search_square_with_reserve.py` - Binary search with reserve constraints

### Advanced Placement Tests
- `test_rectangle_with_center_shape.py` - Dual exclusion zones (corner + center)
- `test_forced_larger_reserve.py` - Testing larger reserve impact on efficiency

All tests generate visual previews with highlighted exclusion zones for algorithm verification.


## 🐛 Troubleshooting

### "File exceeds bin dimensions"
- Check that all images fit within specified bin size
- The application lists all oversized files

### Memory issues with large layouts
- Layouts over 500M pixels may require significant RAM
- 8-bit grayscale mode reduces memory usage by 66%
- For 1000+ images: expect 2-4 GB memory usage with grayscale
- Consider smaller bin dimensions or fewer images for very large datasets

### Can't see grid lines in preview
- Grid lines only appear for square/rectangle shapes
- Circle/ellipse shapes don't display grid lines