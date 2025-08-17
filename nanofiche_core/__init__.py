"""
NanoFiche Core Package
Core functionality for optimal bin packing into envelope shapes.
"""

from .packer import NanoFichePacker, EnvelopeShape, EnvelopeSpec
from .image_bin import ImageBin
from .renderer import NanoFicheRenderer

__all__ = [
    'NanoFichePacker',
    'EnvelopeShape', 
    'EnvelopeSpec',
    'ImageBin',
    'NanoFicheRenderer'
]