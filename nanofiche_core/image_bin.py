"""
Image bin data structure for NanoFiche Image Prep.
"""

from pathlib import Path
from dataclasses import dataclass


@dataclass
class ImageBin:
    """Represents a single image with its bin properties."""
    
    file_path: Path
    width: int
    height: int
    index: int = 0
    
    def __post_init__(self):
        """Ensure file_path is a Path object."""
        if isinstance(self.file_path, str):
            self.file_path = Path(self.file_path)