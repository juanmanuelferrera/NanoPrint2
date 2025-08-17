#!/usr/bin/env python3
"""
NanoFiche Image Prep - Windows Application
Optimal bin packing for raster images into envelope shapes.
"""

import sys
import tkinter as tk
from pathlib import Path

# Add current directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

from nanofiche_core.gui import NanoFicheGUI

def main():
    """Main entry point for NanoFiche Image Prep application."""
    root = tk.Tk()
    app = NanoFicheGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()