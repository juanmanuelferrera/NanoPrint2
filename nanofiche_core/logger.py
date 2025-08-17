"""
Logging system for NanoFiche Image Prep.
Handles comprehensive project logging with timestamps and events.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple


def setup_logging(log_level: int = logging.INFO) -> None:
    """Setup basic logging configuration."""
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )


def log_project(log_path: Path, project_name: str, timestamp: datetime,
                bin_width: int, bin_height: int, envelope_shape: str,
                num_files: int, output_path: Path, final_size: Tuple[int, int],
                process_time: float, approved: bool, images_placed: int,
                error: Optional[str] = None) -> None:
    """
    Log complete project information to file.
    
    Args:
        log_path: Path to log file
        project_name: Name of the project
        timestamp: Start timestamp
        bin_width: Width of each bin
        bin_height: Height of each bin  
        envelope_shape: Shape of envelope
        num_files: Number of input files
        output_path: Path to output TIFF
        final_size: Final canvas dimensions (width, height)
        process_time: Processing time in seconds
        approved: Whether user approved the layout
        images_placed: Number of images successfully placed
        error: Error message if any
    """
    
    log_content = f"""NanoFiche Image Prep - Project Log
{'=' * 50}

Project Information:
    Project Name: {project_name}
    Timestamp: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}
    Status: {"APPROVED" if approved else "REJECTED"}

Input Parameters:
    Bin Dimensions: {bin_width} x {bin_height} pixels
    Envelope Shape: {envelope_shape}
    Input Files: {num_files}
    Images Placed: {images_placed}

Output Information:
    Output Path: {output_path.name}
    Final TIFF Size: {final_size[0]} x {final_size[1]} pixels
    Total Pixels: {final_size[0] * final_size[1]:,}

Process Information:
    Processing Time: {process_time:.2f} seconds
    Completion Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Events:
    {timestamp.strftime('%H:%M:%S')} - Project started
    {timestamp.strftime('%H:%M:%S')} - Input validation completed
    {timestamp.strftime('%H:%M:%S')} - Layout calculation completed
    {timestamp.strftime('%H:%M:%S')} - {"Full" if approved else "Thumbnail"} TIFF generation started
    {datetime.now().strftime('%H:%M:%S')} - Process completed

Configuration:
    Max Canvas Pixels: 500,000,000
    Preview Max Dimension: 4,000 pixels
    Thumbnail Max Dimension: 2,000 pixels
    Output Format: TIFF with LZW compression
    Output DPI: 300

"""

    if error:
        log_content += f"""Error Information:
    Error: {error}
    Status: FAILED

"""

    success_rate = (images_placed / num_files * 100) if num_files > 0 else 0
    status = "SUCCESS" if not error and images_placed == num_files else "PARTIAL" if images_placed > 0 else "FAILED"
    
    log_content += f"""Summary:
    Project: {project_name}
    Files Processed: {images_placed}/{num_files}
    Success Rate: {success_rate:.1f}%
    Final Status: {status}

"""

    # Write to log file
    try:
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write(log_content)
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to write log file {log_path}: {e}")


def generate_log_filename(project_name: str, approved: bool) -> str:
    """
    Generate standardized log filename.
    
    Args:
        project_name: Name of the project
        approved: Whether the layout was approved
        
    Returns:
        Formatted log filename
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    suffix = 'full' if approved else 'thumbnail'
    return f"{project_name}_{timestamp}_{suffix}.log"


def generate_tiff_filename(project_name: str, approved: bool) -> str:
    """
    Generate standardized TIFF filename.
    
    Args:
        project_name: Name of the project
        approved: Whether the layout was approved
        
    Returns:
        Formatted TIFF filename
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    suffix = 'full' if approved else 'thumbnail'
    return f"{project_name}_{timestamp}_{suffix}.tif"