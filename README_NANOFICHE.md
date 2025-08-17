# NanoFiche Image Prep

Windows application for optimal bin packing of raster images into various envelope shapes.

## Features

- **Optimal Bin Packing**: Efficiently arrange fixed-size image bins into envelope shapes
- **Multiple Envelope Shapes**: Square, Rectangle, Circle, and Ellipse with customizable aspect ratios
- **Image Validation**: Automatic checking of image dimensions against bin limits
- **Preview Generation**: Downsampled preview (max 4000px) before committing to full resolution
- **Approval Workflow**: Review and approve layouts before generating final TIFF
- **Comprehensive Logging**: Detailed project logs with timestamps, parameters, and results

## Installation

### Option 1: Download Pre-built EXE (Recommended)

1. Go to the [Releases](https://github.com/your-username/your-repo/releases) page
2. Download `NanoFiche_Image_Prep.exe` from the latest release
3. Run the executable - no installation required!

### Option 2: Build from Source

Requirements:
- Python 3.8 or later
- pip

```bash
# Clone the repository
git clone https://github.com/your-username/your-repo.git
cd your-repo

# Install dependencies
pip install -r requirements.txt

# Run the application
python nanofiche_image_prep.py

# Or build your own EXE
pyinstaller nanofiche_image_prep.spec
```

## Usage

1. **Project Name**: Enter a name for your project
2. **Bin Dimensions**: Set the width (a) and height (b) in pixels for each image bin
3. **Envelope Shape**: Choose from:
   - Square: Equal sides
   - Rectangle: Specify aspect ratio (x:y)
   - Circle: Circular arrangement
   - Ellipse: Specify aspect ratio (x:y)
4. **Select Folders**:
   - Browse to folder containing raster images
   - Browse to output location for TIFF and log files
5. **Validate & Calculate**: Check images and calculate optimal packing
6. **Generate Preview**: Create downsampled preview for review
7. **Approve/Reject**:
   - Approve: Generate full resolution TIFF
   - Reject: Generate thumbnail TIFF only

## Supported Image Formats

- PNG
- JPG/JPEG
- TIFF/TIF
- BMP

## Output Files

- **Full TIFF**: `[project_name]_[timestamp]_full.tif` - Full resolution output
- **Thumbnail**: `[project_name]_[timestamp]_thumbnail.tif` - Reduced size for rejected layouts
- **Log File**: `[project_name]_[timestamp]_[full|thumbnail].log` - Comprehensive project log

## Building EXE with GitHub Actions

This repository includes automated EXE building:

1. Push to `main` branch or create a tag starting with `v` (e.g., `v1.0.0`)
2. GitHub Actions will automatically build the Windows executable
3. Download from Actions artifacts or Releases page

To create a release:
```bash
git tag v1.0.0
git push origin v1.0.0
```

## Algorithm Details

The application uses sophisticated packing algorithms:

- **Rectangle/Square**: Grid-based optimization minimizing area while maintaining aspect ratio
- **Circle/Ellipse**: Spiral placement pattern for optimal space utilization
- Automatic centering within envelope boundaries
- Maintains original image aspect ratios within bins

## Troubleshooting

### "File exceeds bin dimensions" error
- Ensure all images fit within the specified bin dimensions
- The application will list oversized files

### Large canvas warning
- For layouts exceeding 500 million pixels, processing may be slow
- Consider using smaller bin dimensions or fewer images

### Memory issues
- Very large layouts may require significant RAM
- Close other applications if needed

## License

This project is provided as-is for use with the NanoFiche/MicroFiche digitization workflow.