#!/usr/bin/env python3
"""Test file sorting fix."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from pathlib import Path
import re
import glob

def test_file_sorting():
    """Test file sorting behavior."""
    
    dataset_path = Path("/Users/juanmanuelferreradiaz/Downloads/tif200")
    if not dataset_path.exists():
        print("Dataset not found!")
        return
        
    # Get all tif files
    tif_files = list(dataset_path.glob("*.tif"))
    
    print(f"Found {len(tif_files)} TIF files")
    
    # Test alphabetical sorting (current bug)
    alpha_sorted = sorted(tif_files)
    print(f"\nAlphabetical sorting (BUGGY):")
    print(f"First 10: {[f.name for f in alpha_sorted[:10]]}")
    print(f"Last 10: {[f.name for f in alpha_sorted[-10:]]}")
    
    # Test natural numerical sorting (fix)
    def natural_sort_key(path):
        """Extract numeric part from filename for proper sorting."""
        filename = path.name
        # Look for numbers in filename
        numbers = re.findall(r'\d+', filename)
        if numbers:
            # Use the last number found (most specific)
            return int(numbers[-1])
        return 0
    
    natural_sorted = sorted(tif_files, key=natural_sort_key)
    print(f"\nNumerical sorting (FIXED):")
    print(f"First 10: {[f.name for f in natural_sorted[:10]]}")
    print(f"Last 10: {[f.name for f in natural_sorted[-10:]]}")
    
    # Find the file that would be misplaced
    for i, (alpha, natural) in enumerate(zip(alpha_sorted, natural_sorted)):
        if alpha != natural:
            print(f"\nFirst difference at position {i}:")
            print(f"  Alphabetical: {alpha.name}")
            print(f"  Numerical: {natural.name}")
            break
    
    # Check if last file appears early in alphabetical sort
    last_natural = natural_sorted[-1]
    alpha_position = alpha_sorted.index(last_natural)
    print(f"\nLast file analysis:")
    print(f"  File: {last_natural.name}")
    print(f"  Correct position: {len(natural_sorted)} (last)")
    print(f"  Alphabetical position: {alpha_position + 1}")
    
    if alpha_position < 100:  # If last file appears in first 100
        print(f"  ⚠️  CONFIRMED BUG: Last file appears at position {alpha_position + 1} instead of {len(natural_sorted)}")
        print(f"     This explains why yellow (last) image appears in first row!")

if __name__ == "__main__":
    test_file_sorting()