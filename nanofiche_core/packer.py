"""
Optimal packing algorithms for NanoFiche Image Prep.
Handles square, rectangle, circle, and ellipse envelope shapes.
"""

import math
from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple, Optional
import logging


class EnvelopeShape(Enum):
    """Supported envelope shapes."""
    SQUARE = "square"
    RECTANGLE = "rectangle"
    CIRCLE = "circle"
    ELLIPSE = "ellipse"


@dataclass
class EnvelopeSpec:
    """Envelope shape specification."""
    shape: EnvelopeShape
    aspect_x: float = 1.0  # Width aspect ratio
    aspect_y: float = 1.0  # Height aspect ratio
    
    def __post_init__(self):
        """Validate and normalize aspect ratios."""
        if self.shape == EnvelopeShape.SQUARE:
            self.aspect_x = 1.0
            self.aspect_y = 1.0
        elif self.shape == EnvelopeShape.CIRCLE:
            self.aspect_x = 1.0
            self.aspect_y = 1.0


@dataclass
class PackingResult:
    """Result of optimal packing calculation."""
    rows: int
    columns: int
    canvas_width: int
    canvas_height: int
    placements: List[Tuple[int, int]]  # (x, y) coordinates for each bin
    envelope_shape: EnvelopeShape
    total_bins: int
    bin_width: int
    bin_height: int


class NanoFichePacker:
    """Optimal bin packing engine for various envelope shapes."""
    
    def __init__(self, bin_width: int, bin_height: int):
        """
        Initialize packer with bin dimensions.
        
        Args:
            bin_width: Width of each bin in pixels
            bin_height: Height of each bin in pixels
        """
        self.bin_width = bin_width
        self.bin_height = bin_height
        self.logger = logging.getLogger(__name__)
    
    def pack(self, num_bins: int, envelope_spec: EnvelopeSpec) -> PackingResult:
        """
        Calculate optimal packing for given number of bins and envelope shape.
        
        Args:
            num_bins: Number of bins to pack
            envelope_spec: Envelope shape specification
            
        Returns:
            PackingResult with optimal layout
        """
        self.logger.info(f"Packing {num_bins} bins into {envelope_spec.shape.value} envelope")
        
        if envelope_spec.shape == EnvelopeShape.SQUARE:
            return self._pack_square(num_bins)
        elif envelope_spec.shape == EnvelopeShape.RECTANGLE:
            return self._pack_rectangle(num_bins, envelope_spec.aspect_x, envelope_spec.aspect_y)
        elif envelope_spec.shape == EnvelopeShape.CIRCLE:
            return self._pack_circle(num_bins)
        elif envelope_spec.shape == EnvelopeShape.ELLIPSE:
            return self._pack_ellipse(num_bins, envelope_spec.aspect_x, envelope_spec.aspect_y)
        else:
            raise ValueError(f"Unsupported envelope shape: {envelope_spec.shape}")
    
    def _pack_square(self, num_bins: int) -> PackingResult:
        """Pack bins into a square envelope."""
        # Find optimal square grid
        side = math.ceil(math.sqrt(num_bins))
        rows = side
        columns = side
        
        canvas_width = columns * self.bin_width
        canvas_height = rows * self.bin_height
        
        # Generate placements
        placements = []
        for i in range(num_bins):
            row = i // columns
            col = i % columns
            x = col * self.bin_width
            y = row * self.bin_height
            placements.append((x, y))
        
        return PackingResult(
            rows=rows,
            columns=columns,
            canvas_width=canvas_width,
            canvas_height=canvas_height,
            placements=placements,
            envelope_shape=EnvelopeShape.SQUARE,
            total_bins=num_bins,
            bin_width=self.bin_width,
            bin_height=self.bin_height
        )
    
    def _pack_rectangle(self, num_bins: int, aspect_x: float, aspect_y: float) -> PackingResult:
        """Pack bins into a rectangular envelope with given aspect ratio."""
        # Calculate target aspect ratio
        target_aspect = aspect_x / aspect_y
        
        # Find optimal grid arrangement
        best_rows, best_cols = self._find_optimal_grid(num_bins, target_aspect)
        
        # Adjust canvas to exact aspect ratio
        grid_width = best_cols * self.bin_width
        grid_height = best_rows * self.bin_height
        
        # Adjust to exact aspect ratio by scaling the envelope
        if grid_width / grid_height > target_aspect:
            # Grid is too wide, adjust height
            canvas_width = grid_width
            canvas_height = int(grid_width / target_aspect)
        else:
            # Grid is too tall, adjust width
            canvas_height = grid_height
            canvas_width = int(grid_height * target_aspect)
        
        # Generate placements (centered within envelope)
        placements = []
        offset_x = (canvas_width - grid_width) // 2
        offset_y = (canvas_height - grid_height) // 2
        
        for i in range(num_bins):
            row = i // best_cols
            col = i % best_cols
            x = offset_x + col * self.bin_width
            y = offset_y + row * self.bin_height
            placements.append((x, y))
        
        return PackingResult(
            rows=best_rows,
            columns=best_cols,
            canvas_width=canvas_width,
            canvas_height=canvas_height,
            placements=placements,
            envelope_shape=EnvelopeShape.RECTANGLE,
            total_bins=num_bins,
            bin_width=self.bin_width,
            bin_height=self.bin_height
        )
    
    def _pack_circle(self, num_bins: int) -> PackingResult:
        """Pack bins into a circular envelope."""
        # Use spiral packing or concentric circles for optimal arrangement
        # For simplicity, start with square grid inscribed in circle
        
        # Estimate required radius
        bin_area = self.bin_width * self.bin_height
        total_area = num_bins * bin_area
        radius = math.sqrt(total_area / math.pi)
        
        # Find grid that fits in circle
        diameter = 2 * radius
        max_cols = int(diameter / self.bin_width)
        max_rows = int(diameter / self.bin_height)
        
        # Adjust to fit all bins
        while max_cols * max_rows < num_bins:
            radius *= 1.1
            diameter = 2 * radius
            max_cols = int(diameter / self.bin_width)
            max_rows = int(diameter / self.bin_height)
        
        canvas_size = int(diameter)
        center_x = center_y = canvas_size // 2
        
        # Generate placements in spiral pattern
        placements = self._generate_spiral_placements(num_bins, center_x, center_y, radius)
        
        return PackingResult(
            rows=max_rows,
            columns=max_cols,
            canvas_width=canvas_size,
            canvas_height=canvas_size,
            placements=placements,
            envelope_shape=EnvelopeShape.CIRCLE,
            total_bins=num_bins,
            bin_width=self.bin_width,
            bin_height=self.bin_height
        )
    
    def _pack_ellipse(self, num_bins: int, aspect_x: float, aspect_y: float) -> PackingResult:
        """Pack bins into an elliptical envelope."""
        # Similar to circle but with different radii
        bin_area = self.bin_width * self.bin_height
        total_area = num_bins * bin_area
        
        # Calculate ellipse parameters
        aspect_ratio = aspect_x / aspect_y
        
        # Estimate radii
        # Area = π * a * b, where a/b = aspect_ratio
        b = math.sqrt(total_area / (math.pi * aspect_ratio))
        a = b * aspect_ratio
        
        canvas_width = int(2 * a)
        canvas_height = int(2 * b)
        center_x = canvas_width // 2
        center_y = canvas_height // 2
        
        # Generate placements in elliptical pattern
        placements = self._generate_elliptical_placements(num_bins, center_x, center_y, a, b)
        
        return PackingResult(
            rows=int(canvas_height / self.bin_height),
            columns=int(canvas_width / self.bin_width),
            canvas_width=canvas_width,
            canvas_height=canvas_height,
            placements=placements,
            envelope_shape=EnvelopeShape.ELLIPSE,
            total_bins=num_bins,
            bin_width=self.bin_width,
            bin_height=self.bin_height
        )
    
    def _find_optimal_grid(self, num_bins: int, target_aspect: float) -> Tuple[int, int]:
        """Find optimal rows/columns for rectangular packing."""
        best_score = float('inf')
        best_rows = best_cols = 1
        
        # Test all possible factorizations
        for rows in range(1, num_bins + 1):
            if num_bins % rows == 0:
                cols = num_bins // rows
            else:
                cols = math.ceil(num_bins / rows)
            
            # Calculate grid dimensions
            grid_width = cols * self.bin_width
            grid_height = rows * self.bin_height
            grid_aspect = grid_width / grid_height
            
            # Score based on how close to target aspect ratio
            aspect_error = abs(grid_aspect - target_aspect)
            area = grid_width * grid_height
            
            # Combine aspect error and area (prefer smaller area)
            score = aspect_error + (area / 1000000)  # Normalize area
            
            if score < best_score:
                best_score = score
                best_rows = rows
                best_cols = cols
        
        return best_rows, best_cols
    
    def _generate_spiral_placements(self, num_bins: int, center_x: int, center_y: int, radius: float) -> List[Tuple[int, int]]:
        """Generate spiral placement pattern for circular envelope."""
        placements = []
        
        # Start from center and spiral outward
        for i in range(num_bins):
            # Calculate spiral position
            angle = i * 0.5  # Adjust for tighter/looser spiral
            r = (i / num_bins) * radius * 0.8  # Don't use full radius
            
            x = center_x + int(r * math.cos(angle)) - self.bin_width // 2
            y = center_y + int(r * math.sin(angle)) - self.bin_height // 2
            
            # Ensure within bounds
            x = max(0, min(x, center_x * 2 - self.bin_width))
            y = max(0, min(y, center_y * 2 - self.bin_height))
            
            placements.append((x, y))
        
        return placements
    
    def _generate_elliptical_placements(self, num_bins: int, center_x: int, center_y: int, a: float, b: float) -> List[Tuple[int, int]]:
        """Generate placement pattern for elliptical envelope."""
        placements = []
        
        # Similar to spiral but with elliptical coordinates
        for i in range(num_bins):
            angle = i * 0.5
            r = (i / num_bins) * 0.8  # Relative radius
            
            # Convert to elliptical coordinates
            x = center_x + int(r * a * math.cos(angle)) - self.bin_width // 2
            y = center_y + int(r * b * math.sin(angle)) - self.bin_height // 2
            
            # Ensure within bounds
            x = max(0, min(x, center_x * 2 - self.bin_width))
            y = max(0, min(y, center_y * 2 - self.bin_height))
            
            placements.append((x, y))
        
        return placements