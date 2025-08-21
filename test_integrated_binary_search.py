#!/usr/bin/env python3

import sys
import os

# Add the nanofiche_core directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'nanofiche_core'))

from nanofiche_core.packer import NanoFichePacker, EnvelopeSpec, EnvelopeShape

def test_integrated_binary_search():
    """Test the integrated binary envelope search algorithm."""
    
    # Create packer instance with standard bin dimensions
    packer = NanoFichePacker(bin_width=1300, bin_height=1900)
    
    # Create envelope spec for circle with square reserve
    envelope_spec = EnvelopeSpec(
        shape=EnvelopeShape.CIRCLE_WITH_SQUARE_RESERVE,
        square_reserve_size=10000
    )
    
    # Test with smaller number of bins for quick validation
    num_bins = 100
    
    try:
        # Call the integrated packing method
        result = packer.pack(num_bins, envelope_spec)
        
        print(f"✅ Integration test successful!")
        print(f"   Bins requested: {num_bins}")
        print(f"   Placements generated: {len(result.placements)}")
        print(f"   Canvas size: {result.canvas_width}x{result.canvas_height}")
        print(f"   Envelope shape: {result.envelope_shape}")
        
        # Verify all placements were generated
        if len(result.placements) == num_bins:
            print(f"✅ All {num_bins} bins placed successfully")
            return True
        else:
            print(f"❌ Only {len(result.placements)}/{num_bins} bins placed")
            return False
            
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_integrated_binary_search()
    sys.exit(0 if success else 1)