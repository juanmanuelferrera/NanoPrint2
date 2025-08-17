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
- **Smart Validation**: Automatic checking of image dimensions against bin limits
- **Preview System**: Generate downsampled preview (max 4000px) before final rendering
- **Approval Workflow**: Review layouts before generating full resolution TIFF
- **Comprehensive Logging**: Detailed project logs with all parameters and results

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

- `[project]_[timestamp]_full.tif` - Full resolution output
- `[project]_[timestamp]_thumbnail.tif` - Reduced size (rejected layouts)
- `[project]_[timestamp]_[full|thumbnail].log` - Detailed project log

## 🔧 Supported Formats

- PNG
- JPG/JPEG
- TIFF/TIF
- BMP

## 📊 Algorithm Details

The application implements sophisticated packing algorithms:

- **Rectangle Packing**: Optimizes grid layout to match target aspect ratio while minimizing area
- **Circle/Ellipse**: Uses spiral placement for optimal space utilization
- All algorithms maintain original image aspect ratios within bins

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is part of the NanoFiche/MicroFiche digitization workflow.

## 🐛 Troubleshooting

### "File exceeds bin dimensions"
- Check that all images fit within specified bin size
- The application lists all oversized files

### Memory issues with large layouts
- Layouts over 500M pixels may require significant RAM
- Consider smaller bin dimensions or fewer images

### Can't see grid lines in preview
- Grid lines only appear for square/rectangle shapes
- Circle/ellipse shapes don't display grid lines