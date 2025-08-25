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
    CIRCLE_WITH_SQUARE_RESERVE = "circle_with_square_reserve"


@dataclass
class EnvelopeSpec:
    """Envelope shape specification."""
    shape: EnvelopeShape
    aspect_x: float = 1.0  # Width aspect ratio
    aspect_y: float = 1.0  # Height aspect ratio
    square_reserve_size: int = 10000  # Square reserve size in pixels
    reserve_enabled: bool = False  # Enable reserved space
    reserve_width: int = 5000  # Fixed width in pixels
    reserve_height: int = 5000  # Fixed height in pixels
    reserve_position: str = "center"  # "center" or "top-left"
    reserve_auto_size: bool = False  # Auto-optimize reserve size for bottom row fill
    
    def __post_init__(self):
        """Validate and normalize aspect ratios."""
        if self.shape == EnvelopeShape.SQUARE:
            self.aspect_x = 1.0
            self.aspect_y = 1.0
        elif self.shape == EnvelopeShape.CIRCLE:
            self.aspect_x = 1.0
            self.aspect_y = 1.0
        elif self.shape == EnvelopeShape.CIRCLE_WITH_SQUARE_RESERVE:
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
    envelope_spec: EnvelopeSpec = None  # Optional envelope specification for reserved space


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
        if envelope_spec.reserve_enabled:
            self.logger.info(f"Reserved space: {envelope_spec.reserve_width}x{envelope_spec.reserve_height} at {envelope_spec.reserve_position}")
        
        if envelope_spec.shape == EnvelopeShape.SQUARE:
            if envelope_spec.reserve_enabled:
                if envelope_spec.reserve_auto_size and envelope_spec.reserve_position == "top-left":
                    return self._pack_square_with_optimized_reserve(num_bins, envelope_spec)
                return self._pack_square_with_reserve(num_bins, envelope_spec)
            return self._pack_square(num_bins)
        elif envelope_spec.shape == EnvelopeShape.RECTANGLE:
            if envelope_spec.reserve_enabled:
                return self._pack_rectangle_with_reserve(num_bins, envelope_spec)
            return self._pack_rectangle(num_bins, envelope_spec.aspect_x, envelope_spec.aspect_y)
        elif envelope_spec.shape == EnvelopeShape.CIRCLE:
            if envelope_spec.reserve_enabled:
                return self._pack_circle_with_reserve(num_bins, envelope_spec)
            return self._pack_circle(num_bins)
        elif envelope_spec.shape == EnvelopeShape.ELLIPSE:
            return self._pack_ellipse(num_bins, envelope_spec.aspect_x, envelope_spec.aspect_y)
        elif envelope_spec.shape == EnvelopeShape.CIRCLE_WITH_SQUARE_RESERVE:
            return self._pack_circle_with_binary_search(num_bins, envelope_spec.square_reserve_size)
        else:
            raise ValueError(f"Unsupported envelope shape: {envelope_spec.shape}")
    
    def _pack_square(self, num_bins: int) -> PackingResult:
        """Pack bins into a square envelope."""
        # Find optimal square grid
        side = math.ceil(math.sqrt(num_bins))
        rows = side
        columns = side
        
        # Calculate grid dimensions
        grid_width = columns * self.bin_width
        grid_height = rows * self.bin_height
        
        # Force square canvas - use the larger dimension
        canvas_size = max(grid_width, grid_height)
        
        # Center the grid in the square canvas
        offset_x = (canvas_size - grid_width) // 2
        offset_y = (canvas_size - grid_height) // 2
        
        # Generate placements (centered in square canvas)
        placements = []
        for i in range(num_bins):
            row = i // columns
            col = i % columns
            x = offset_x + col * self.bin_width
            y = offset_y + row * self.bin_height
            placements.append((x, y))
        
        return PackingResult(
            rows=rows,
            columns=columns,
            canvas_width=canvas_size,
            canvas_height=canvas_size,
            placements=placements,
            envelope_shape=EnvelopeShape.SQUARE,
            total_bins=num_bins,
            bin_width=self.bin_width,
            bin_height=self.bin_height
        )
    
    def _check_overlap_with_reserve(self, x: int, y: int, envelope_spec: EnvelopeSpec, canvas_width: int, canvas_height: int) -> bool:
        """Check if a bin at position (x, y) overlaps with reserved space."""
        if not envelope_spec.reserve_enabled:
            return False
            
        # Calculate reserve position
        if envelope_spec.reserve_position == "center":
            reserve_x = (canvas_width - envelope_spec.reserve_width) // 2
            reserve_y = (canvas_height - envelope_spec.reserve_height) // 2
        else:  # top-left
            reserve_x = 0
            reserve_y = 0
        
        # Check overlap
        bin_right = x + self.bin_width
        bin_bottom = y + self.bin_height
        reserve_right = reserve_x + envelope_spec.reserve_width
        reserve_bottom = reserve_y + envelope_spec.reserve_height
        
        # No overlap if bin is completely outside reserve
        return not (bin_right <= reserve_x or x >= reserve_right or 
                   bin_bottom <= reserve_y or y >= reserve_bottom)
    
    def _pack_square_with_reserve(self, num_bins: int, envelope_spec: EnvelopeSpec) -> PackingResult:
        """Pack bins into square with reserved space."""
        # Start with normal square size and increase if needed
        side = math.ceil(math.sqrt(num_bins))
        found_solution = False
        max_attempts = 50
        attempts = 0
        
        while not found_solution and attempts < max_attempts:
            rows = side
            columns = side
            grid_width = columns * self.bin_width
            grid_height = rows * self.bin_height
            canvas_size = max(grid_width, grid_height)
            
            # Try to place all bins avoiding reserve
            placements = []
            offset_x = (canvas_size - grid_width) // 2
            offset_y = (canvas_size - grid_height) // 2
            
            for row in range(rows):
                for col in range(columns):
                    if len(placements) >= num_bins:
                        break
                    x = offset_x + col * self.bin_width
                    y = offset_y + row * self.bin_height
                    
                    # Check if this position overlaps with reserve
                    if not self._check_overlap_with_reserve(x, y, envelope_spec, canvas_size, canvas_size):
                        placements.append((x, y))
                
                if len(placements) >= num_bins:
                    break
            
            if len(placements) >= num_bins:
                found_solution = True
            else:
                side += 1  # Increase grid size
                attempts += 1
        
        return PackingResult(
            rows=rows,
            columns=columns,
            canvas_width=canvas_size,
            canvas_height=canvas_size,
            placements=placements[:num_bins],
            envelope_shape=EnvelopeShape.SQUARE,
            total_bins=num_bins,
            bin_width=self.bin_width,
            bin_height=self.bin_height,
            envelope_spec=envelope_spec
        )
    
    def _calculate_optimized_reserve_size(self, side_length: float) -> Tuple[int, int]:
        """Calculate optimized reserve size based on square size and bin aspect ratio."""
        # Use same aspect ratio as bins for reserve
        reserve_aspect_ratio = self.bin_width / self.bin_height
        
        # Reserve area should be roughly 1-2 image areas
        reserve_area = 1.5 * self.bin_width * self.bin_height
        
        # Calculate dimensions with correct aspect ratio
        reserve_height = math.sqrt(reserve_area / reserve_aspect_ratio)
        reserve_width = reserve_height * reserve_aspect_ratio
        
        # Max 20% of side length
        max_dimension = side_length * 0.2
        if reserve_width > max_dimension:
            reserve_width = max_dimension
            reserve_height = reserve_width / reserve_aspect_ratio
        if reserve_height > max_dimension:
            reserve_height = max_dimension
            reserve_width = reserve_height * reserve_aspect_ratio
        
        return int(reserve_width), int(reserve_height)
    
    def _try_pack_square_with_optimized_reserve(self, num_bins: int, side_length: float) -> Tuple[bool, List, Tuple[int, int]]:
        """Try to pack bins in square with optimized top-left reserve."""
        reserve_width, reserve_height = self._calculate_optimized_reserve_size(side_length)
        
        placements = []
        bins_placed = 0
        
        # Area 1: Top-right rectangle
        top_right_width = side_length - reserve_width
        top_right_height = reserve_height
        top_right_cols = int(top_right_width / self.bin_width)
        top_right_rows = int(top_right_height / self.bin_height)
        
        # Place images in top-right area
        for row in range(top_right_rows):
            if bins_placed >= num_bins:
                break
            for col in range(top_right_cols):
                if bins_placed >= num_bins:
                    break
                x = reserve_width + col * self.bin_width
                y = row * self.bin_height
                if x + self.bin_width <= side_length and y + self.bin_height <= reserve_height:
                    placements.append((int(x), int(y)))
                    bins_placed += 1
        
        # Area 2: Bottom rectangle (full width)
        bottom_width = side_length
        bottom_height = side_length - reserve_height
        bottom_cols = int(bottom_width / self.bin_width)
        bottom_rows = int(bottom_height / self.bin_height)
        
        # Place remaining images in bottom area
        for row in range(bottom_rows):
            if bins_placed >= num_bins:
                break
            for col in range(bottom_cols):
                if bins_placed >= num_bins:
                    break
                x = col * self.bin_width
                y = reserve_height + row * self.bin_height
                if x + self.bin_width <= side_length and y + self.bin_height <= side_length:
                    placements.append((int(x), int(y)))
                    bins_placed += 1
        
        success = bins_placed >= num_bins
        return success, placements, (reserve_width, reserve_height)
    
    def _pack_square_with_optimized_reserve(self, num_bins: int, envelope_spec: EnvelopeSpec) -> PackingResult:
        """Pack bins into square with optimized reserved space using binary search."""
        # Binary search for optimal square size
        total_image_area = num_bins * self.bin_width * self.bin_height
        
        # Initial bounds
        side_min = math.sqrt(total_image_area) * 1.0
        side_max = math.sqrt(total_image_area) * 2.0
        
        # Find working upper bound
        while side_max <= math.sqrt(total_image_area) * 3.0:
            success, _, _ = self._try_pack_square_with_optimized_reserve(num_bins, side_max)
            if success:
                break
            side_max += math.sqrt(total_image_area) * 0.2
        
        # Binary search
        best_side = side_max
        best_placements = None
        best_reserve_dims = None
        
        while side_max - side_min > 1:
            side_mid = (side_min + side_max) / 2
            success, placements, reserve_dims = self._try_pack_square_with_optimized_reserve(num_bins, side_mid)
            
            if success:
                best_side = side_mid
                best_placements = placements
                best_reserve_dims = reserve_dims
                side_max = side_mid
            else:
                side_min = side_mid
        
        if best_placements is None:
            # Fallback
            _, best_placements, best_reserve_dims = self._try_pack_square_with_optimized_reserve(num_bins, side_max)
            best_side = side_max
        
        canvas_size = int(best_side)
        
        # Update envelope spec with optimized dimensions
        envelope_spec.reserve_width = best_reserve_dims[0]
        envelope_spec.reserve_height = best_reserve_dims[1]
        
        # Calculate grid info for result
        rows = int(canvas_size / self.bin_height)
        cols = int(canvas_size / self.bin_width)
        
        self.logger.info(f"Optimized square: {canvas_size}x{canvas_size}, reserve: {best_reserve_dims[0]}x{best_reserve_dims[1]}")
        
        return PackingResult(
            rows=rows,
            columns=cols,
            canvas_width=canvas_size,
            canvas_height=canvas_size,
            placements=best_placements[:num_bins],
            envelope_shape=EnvelopeShape.SQUARE,
            total_bins=num_bins,
            bin_width=self.bin_width,
            bin_height=self.bin_height,
            envelope_spec=envelope_spec
        )
    
    def _pack_rectangle_with_reserve(self, num_bins: int, envelope_spec: EnvelopeSpec) -> PackingResult:
        """Pack bins into rectangle with reserved space."""
        target_aspect = envelope_spec.aspect_x / envelope_spec.aspect_y
        
        # Start with optimal grid and increase if needed
        best_rows, best_cols = self._find_optimal_grid(num_bins, target_aspect)
        found_solution = False
        scale_factor = 1.0
        max_scale = 3.0
        
        while not found_solution and scale_factor <= max_scale:
            rows = max(best_rows, int(best_rows * scale_factor))
            cols = max(best_cols, int(best_cols * scale_factor))
            
            grid_width = cols * self.bin_width
            grid_height = rows * self.bin_height
            
            # Adjust to exact aspect ratio
            if grid_width / grid_height > target_aspect:
                canvas_width = grid_width
                canvas_height = int(grid_width / target_aspect)
            else:
                canvas_height = grid_height
                canvas_width = int(grid_height * target_aspect)
            
            # Try to place all bins avoiding reserve
            placements = []
            offset_x = (canvas_width - grid_width) // 2
            offset_y = (canvas_height - grid_height) // 2
            
            for row in range(rows):
                for col in range(cols):
                    if len(placements) >= num_bins:
                        break
                    x = offset_x + col * self.bin_width
                    y = offset_y + row * self.bin_height
                    
                    # Check if this position overlaps with reserve
                    if not self._check_overlap_with_reserve(x, y, envelope_spec, canvas_width, canvas_height):
                        placements.append((x, y))
                
                if len(placements) >= num_bins:
                    break
            
            if len(placements) >= num_bins:
                found_solution = True
            else:
                scale_factor += 0.1  # Increase grid size
        
        return PackingResult(
            rows=rows,
            columns=cols,
            canvas_width=canvas_width,
            canvas_height=canvas_height,
            placements=placements[:num_bins],
            envelope_shape=EnvelopeShape.RECTANGLE,
            total_bins=num_bins,
            bin_width=self.bin_width,
            bin_height=self.bin_height,
            envelope_spec=envelope_spec
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
        """Pack bins into a circular envelope using circular-constrained grid layout."""
        
        # Start with an estimate and iteratively find the best fit
        # We want a circle that can fit all bins while maintaining circular shape
        
        # Calculate area needed and estimate circle size
        bin_area = self.bin_width * self.bin_height
        total_area = num_bins * bin_area * 1.5  # Add 50% overhead for circular packing
        estimated_radius = math.sqrt(total_area / math.pi)
        
        # Try different grid arrangements to find one that fits in circle
        best_radius = None
        best_grid_size = None
        
        # Try grid sizes from square down to more elongated rectangles
        for grid_side in range(math.ceil(math.sqrt(num_bins)), max(1, int(math.sqrt(num_bins) * 0.5)), -1):
            rows = math.ceil(num_bins / grid_side)
            cols = grid_side
            
            # Calculate inscribed rectangle that fits in circle
            grid_width = cols * self.bin_width
            grid_height = rows * self.bin_height
            
            # Find minimum radius to fit this grid as inscribed rectangle
            # Use diagonal divided by 2, then add margin
            grid_diagonal = math.sqrt(grid_width**2 + grid_height**2)
            required_radius = grid_diagonal / 2 * 1.2  # 20% margin
            
            if best_radius is None or required_radius < best_radius:
                best_radius = required_radius
                best_grid_size = (rows, cols)
        
        if best_grid_size is None:
            # Fallback to square
            side = math.ceil(math.sqrt(num_bins))
            best_grid_size = (side, side)
            grid_diagonal = math.sqrt((side * self.bin_width)**2 + (side * self.bin_height)**2)
            best_radius = grid_diagonal / 2 * 1.2
        
        canvas_size = int(2 * best_radius)
        center_x = center_y = canvas_size // 2
        rows, cols = best_grid_size
        
        # Generate circular grid placements
        placements = self._generate_circular_grid_placements(num_bins, rows, cols, center_x, center_y)
        
        return PackingResult(
            rows=rows,
            columns=cols,
            canvas_width=canvas_size,
            canvas_height=canvas_size,
            placements=placements,
            envelope_shape=EnvelopeShape.CIRCLE,
            total_bins=num_bins,
            bin_width=self.bin_width,
            bin_height=self.bin_height
        )
    
    def _check_inside_circle_avoiding_reserve(self, x: int, y: int, center_x: float, center_y: float, 
                                              radius: float, envelope_spec: EnvelopeSpec) -> bool:
        """Check if a bin position is valid: inside circle but outside reserved space (optimized version)."""
        # Use tile center for circle check (like original algorithm)
        tile_center_x = x + self.bin_width // 2
        tile_center_y = y + self.bin_height // 2
        distance_from_center = math.sqrt((tile_center_x - center_x)**2 + (tile_center_y - center_y)**2)
        
        if distance_from_center > radius:
            return False  # Outside circle
        
        # Check if overlaps with square reserve (always center for circles)
        if envelope_spec.reserve_enabled:
            square_half_size = envelope_spec.reserve_width // 2  # Assume square reserve
            square_left = center_x - square_half_size
            square_right = center_x + square_half_size
            square_top = center_y - square_half_size
            square_bottom = center_y + square_half_size
            
            # Tile bounds
            tile_left = x
            tile_right = x + self.bin_width
            tile_top = y
            tile_bottom = y + self.bin_height
            
            # Check if tile overlaps with square reserve
            if not (tile_right <= square_left or tile_left >= square_right or 
                   tile_bottom <= square_top or tile_top >= square_bottom):
                return False  # Overlaps with square reserve
        
        return True
    
    def _pack_circle_with_reserve_optimized(self, num_bins: int, radius: float, envelope_spec: EnvelopeSpec) -> Tuple[List[Tuple[int, int]], bool]:
        """Pack images row-by-row in circle with square reserve (optimized algorithm)."""
        canvas_size = int(2 * radius)
        center_x = center_y = canvas_size // 2
        
        placements = []
        images_placed = 0
        
        # Go row by row from top to bottom (like original)
        current_y = 0
        
        while images_placed < num_bins and current_y + self.bin_height <= canvas_size:
            # Place images left to right in this row
            current_x = 0
            
            while images_placed < num_bins and current_x + self.bin_width <= canvas_size:
                # Check if this position is valid
                if self._check_inside_circle_avoiding_reserve(current_x, current_y, center_x, center_y, radius, envelope_spec):
                    placements.append((current_x, current_y))
                    images_placed += 1
                
                current_x += self.bin_width
            
            current_y += self.bin_height
        
        # Check if all images fit
        all_images_fit = (images_placed == num_bins)
        return placements, all_images_fit
    
    def _pack_circle_with_reserve(self, num_bins: int, envelope_spec: EnvelopeSpec) -> PackingResult:
        """Pack bins into circle with reserved space using optimized binary search (93.9% efficiency algorithm)."""
        # Step 1: Calculate image area
        image_area = num_bins * self.bin_width * self.bin_height
        self.logger.info(f"Optimized circle packing: image area = {image_area:,} pixels²")
        
        # Step 2: Start with envelope area same as image area
        # For circle: area = π * r², so r = sqrt(area / π)
        min_radius = math.sqrt(image_area / math.pi)
        max_radius = math.sqrt(image_area * 3 / math.pi)  # Up to 3x area
        
        self.logger.info(f"Binary search bounds: min_radius={min_radius:.1f}, max_radius={max_radius:.1f}")
        
        best_radius = None
        best_placements = None
        iteration = 0
        
        # Binary search loop with 1-pixel precision (like original)
        while max_radius - min_radius > 1.0:
            iteration += 1
            test_radius = (min_radius + max_radius) / 2
            test_area = math.pi * test_radius * test_radius
            
            # Pack images and check if any go outside envelope
            placements, all_fit = self._pack_circle_with_reserve_optimized(num_bins, test_radius, envelope_spec)
            
            if all_fit:
                # If inside then decrease envelope area
                self.logger.info(f"Iteration {iteration}: radius={test_radius:.1f} ✓ All {len(placements)} images fit")
                max_radius = test_radius
                best_radius = test_radius
                best_placements = placements
            else:
                # If outside then increase envelope area
                self.logger.info(f"Iteration {iteration}: radius={test_radius:.1f} ✗ Only {len(placements)}/{num_bins} fit")
                min_radius = test_radius
        
        # Use the last working radius
        if best_radius is None:
            best_radius = max_radius
            best_placements, _ = self._pack_circle_with_reserve_optimized(num_bins, best_radius, envelope_spec)
        
        final_canvas_size = int(2 * best_radius)
        final_envelope_area = math.pi * best_radius * best_radius
        efficiency = image_area / final_envelope_area * 100
        
        self.logger.info(f"Optimized result: radius={best_radius:.1f}, efficiency={efficiency:.1f}%")
        
        # Calculate grid dimensions for compatibility
        rows = int(final_canvas_size / self.bin_height)
        cols = int(final_canvas_size / self.bin_width)
        
        return PackingResult(
            rows=rows,
            columns=cols,
            canvas_width=final_canvas_size,
            canvas_height=final_canvas_size,
            placements=best_placements,
            envelope_shape=EnvelopeShape.CIRCLE,
            total_bins=num_bins,
            bin_width=self.bin_width,
            bin_height=self.bin_height,
            envelope_spec=envelope_spec
        )
    
    def _pack_ellipse(self, num_bins: int, aspect_x: float, aspect_y: float) -> PackingResult:
        """Pack bins into an elliptical envelope using column optimization like circle method."""
        
        # Calculate area needed and estimate ellipse size
        bin_area = self.bin_width * self.bin_height
        total_area = num_bins * bin_area * 1.6  # Overhead for elliptical packing
        
        aspect_ratio = aspect_x / aspect_y
        
        # Calculate ellipse radii: Area = π * a * b, where a/b = aspect_ratio
        b = math.sqrt(total_area / (math.pi * aspect_ratio))
        a = b * aspect_ratio
        
        # Try different grid arrangements to find one that fits efficiently in ellipse
        best_radii = None
        best_grid_size = None
        best_efficiency = 0
        
        # Try grid sizes with column optimization like circle method
        max_grid_side = int(math.sqrt(num_bins) * 1.5)
        min_grid_side = max(1, int(math.sqrt(num_bins) * 0.6))
        
        for cols in range(min_grid_side, max_grid_side + 1):
            rows = math.ceil(num_bins / cols)
            
            # Calculate grid dimensions
            grid_width = cols * self.bin_width
            grid_height = rows * self.bin_height
            
            # For ellipse, find minimum radii to fit this grid
            # Use inscribed rectangle approach but adapted for ellipse
            grid_aspect = grid_width / grid_height
            
            # Calculate required ellipse radii to inscribe this rectangle
            # For rectangle (w,h) inscribed in ellipse (a,b): w²/a² + h²/b² = 4
            # We know aspect_ratio = a/b, so solve for a and b
            if aspect_ratio > 1:  # Wider ellipse
                required_b = grid_height / 2 * 1.1  # 10% margin
                required_a = required_b * aspect_ratio
            else:  # Taller ellipse
                required_a = grid_width / 2 * 1.1  # 10% margin
                required_b = required_a / aspect_ratio
            
            # Calculate efficiency (bins per unit area)
            ellipse_area = math.pi * required_a * required_b
            efficiency = num_bins / ellipse_area
            
            # Prefer arrangements that match the target aspect ratio better
            aspect_match = 1.0 / (1.0 + abs(grid_aspect - aspect_ratio))
            combined_score = efficiency * aspect_match
            
            if combined_score > best_efficiency:
                best_efficiency = combined_score
                best_radii = (required_a, required_b)
                best_grid_size = (rows, cols)
        
        if best_grid_size is None:
            # Fallback to square arrangement
            side = math.ceil(math.sqrt(num_bins))
            best_grid_size = (side, side)
            grid_diagonal = math.sqrt((side * self.bin_width)**2 + (side * self.bin_height)**2)
            avg_radius = grid_diagonal / 2 * 1.2
            if aspect_ratio > 1:
                best_radii = (avg_radius * aspect_ratio, avg_radius)
            else:
                best_radii = (avg_radius, avg_radius / aspect_ratio)
        
        a, b = best_radii
        canvas_width = int(2 * a)
        canvas_height = int(2 * b)
        center_x = canvas_width // 2
        center_y = canvas_height // 2
        rows, cols = best_grid_size
        
        # Generate elliptical placements with constraint checking
        placements = self._generate_elliptical_constrained_placements(
            num_bins, rows, cols, center_x, center_y, a, b
        )
        
        return PackingResult(
            rows=rows,
            columns=cols,
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
    
    def _generate_elliptical_constrained_placements(self, num_bins: int, rows: int, cols: int,
                                                  center_x: int, center_y: int, a: float, b: float) -> List[Tuple[int, int]]:
        """Generate elliptical placement that only places bins within ellipse boundary."""
        placements = []
        
        # Calculate grid dimensions
        grid_width = cols * self.bin_width
        grid_height = rows * self.bin_height
        
        # Center the grid
        start_x = center_x - grid_width // 2
        start_y = center_y - grid_height // 2
        
        bins_placed = 0
        
        # Place bins row by row, but only if they fit in ellipse
        for row in range(rows):
            if bins_placed >= num_bins:
                break
                
            for col in range(cols):
                if bins_placed >= num_bins:
                    break
                
                # Calculate bin position
                x = start_x + col * self.bin_width
                y = start_y + row * self.bin_height
                
                # Calculate bin center
                bin_center_x = x + self.bin_width // 2
                bin_center_y = y + self.bin_height // 2
                
                # Check if bin center is within ellipse
                # Ellipse equation: ((x-cx)/a)² + ((y-cy)/b)² ≤ 1
                ellipse_test = ((bin_center_x - center_x) / a) ** 2 + ((bin_center_y - center_y) / b) ** 2
                
                if ellipse_test <= 0.8:  # Use 80% of ellipse for better fit
                    placements.append((x, y))
                    bins_placed += 1
        
        # If we haven't placed all bins, place remaining ones in spiral within ellipse
        if bins_placed < num_bins:
            remaining_placements = self._generate_spiral_placements_elliptical(
                num_bins - bins_placed, center_x, center_y, a * 0.7, b * 0.7, start_index=bins_placed
            )
            placements.extend(remaining_placements)
        
        return placements
    
    def _generate_elliptical_placements(self, num_bins: int, center_x: int, center_y: int, a: float, b: float) -> List[Tuple[int, int]]:
        """Generate placement pattern for elliptical envelope with simple grid layout."""
        placements = []
        
        # Use simple rectangular grid that fits within the ellipse, similar to rectangle packing
        # Calculate optimal grid arrangement first
        target_aspect = a / b
        best_rows, best_cols = self._find_optimal_grid(num_bins, target_aspect)
        
        # Calculate grid dimensions
        grid_width = best_cols * self.bin_width
        grid_height = best_rows * self.bin_height
        
        # Center the grid in the ellipse canvas
        start_x = center_x - grid_width // 2
        start_y = center_y - grid_height // 2
        
        # Place bins in simple grid pattern (left-to-right, top-to-bottom)
        for i in range(num_bins):
            row = i // best_cols
            col = i % best_cols
            
            x = start_x + col * self.bin_width
            y = start_y + row * self.bin_height
            
            # Ensure within canvas bounds
            x = max(0, min(x, center_x * 2 - self.bin_width))
            y = max(0, min(y, center_y * 2 - self.bin_height))
            
            placements.append((x, y))
        
        return placements
    
    def _generate_elliptical_constrained_placements(self, num_bins: int, rows: int, cols: int,
                                                  center_x: int, center_y: int, a: float, b: float) -> List[Tuple[int, int]]:
        """Generate elliptical placement that only places bins within ellipse boundary."""
        placements = []
        
        # Calculate grid dimensions
        grid_width = cols * self.bin_width
        grid_height = rows * self.bin_height
        
        # Center the grid
        start_x = center_x - grid_width // 2
        start_y = center_y - grid_height // 2
        
        bins_placed = 0
        
        # Place bins row by row, but only if they fit in ellipse
        for row in range(rows):
            if bins_placed >= num_bins:
                break
                
            for col in range(cols):
                if bins_placed >= num_bins:
                    break
                
                # Calculate bin position
                x = start_x + col * self.bin_width
                y = start_y + row * self.bin_height
                
                # Calculate bin center
                bin_center_x = x + self.bin_width // 2
                bin_center_y = y + self.bin_height // 2
                
                # Check if bin center is within ellipse
                # Ellipse equation: ((x-cx)/a)² + ((y-cy)/b)² ≤ 1
                ellipse_test = ((bin_center_x - center_x) / a) ** 2 + ((bin_center_y - center_y) / b) ** 2
                
                if ellipse_test <= 0.8:  # Use 80% of ellipse for better fit
                    placements.append((x, y))
                    bins_placed += 1
        
        # If we haven't placed all bins, place remaining ones in spiral within ellipse
        if bins_placed < num_bins:
            remaining_placements = self._generate_spiral_placements_elliptical(
                num_bins - bins_placed, center_x, center_y, a * 0.7, b * 0.7, start_index=bins_placed
            )
            placements.extend(remaining_placements)
        
        return placements
    
    def _generate_spiral_placements_elliptical(self, num_bins: int, center_x: int, center_y: int, 
                                             a: float, b: float, start_index: int = 0) -> List[Tuple[int, int]]:
        """Generate spiral placement pattern for remaining bins in elliptical envelope."""
        placements = []
        
        for i in range(num_bins):
            # Use spiral pattern similar to circle but with elliptical scaling
            angle = (start_index + i) * 0.5
            r = ((start_index + i) / (start_index + num_bins)) * 0.8
            
            # Convert to elliptical coordinates
            x = center_x + int(r * a * math.cos(angle)) - self.bin_width // 2
            y = center_y + int(r * b * math.sin(angle)) - self.bin_height // 2
            
            # Ensure within bounds
            x = max(0, min(x, center_x * 2 - self.bin_width))
            y = max(0, min(y, center_y * 2 - self.bin_height))
            
            placements.append((x, y))
        
        return placements
    
    def _generate_elliptical_constrained_placements(self, num_bins: int, rows: int, cols: int,
                                                  center_x: int, center_y: int, a: float, b: float) -> List[Tuple[int, int]]:
        """Generate elliptical placement that only places bins within ellipse boundary."""
        placements = []
        
        # Calculate grid dimensions
        grid_width = cols * self.bin_width
        grid_height = rows * self.bin_height
        
        # Center the grid
        start_x = center_x - grid_width // 2
        start_y = center_y - grid_height // 2
        
        bins_placed = 0
        
        # Place bins row by row, but only if they fit in ellipse
        for row in range(rows):
            if bins_placed >= num_bins:
                break
                
            for col in range(cols):
                if bins_placed >= num_bins:
                    break
                
                # Calculate bin position
                x = start_x + col * self.bin_width
                y = start_y + row * self.bin_height
                
                # Calculate bin center
                bin_center_x = x + self.bin_width // 2
                bin_center_y = y + self.bin_height // 2
                
                # Check if bin center is within ellipse
                # Ellipse equation: ((x-cx)/a)² + ((y-cy)/b)² ≤ 1
                ellipse_test = ((bin_center_x - center_x) / a) ** 2 + ((bin_center_y - center_y) / b) ** 2
                
                if ellipse_test <= 0.8:  # Use 80% of ellipse for better fit
                    placements.append((x, y))
                    bins_placed += 1
        
        # If we haven't placed all bins, place remaining ones in spiral within ellipse
        if bins_placed < num_bins:
            remaining_placements = self._generate_spiral_placements_elliptical(
                num_bins - bins_placed, center_x, center_y, a * 0.7, b * 0.7, start_index=bins_placed
            )
            placements.extend(remaining_placements)
        
        return placements
    
    def _generate_circular_grid_placements(self, num_bins: int, rows: int, cols: int, 
                                         center_x: int, center_y: int) -> List[Tuple[int, int]]:
        """Generate circular layout using row-by-row approach optimized for minimal envelope area."""
        
        # Calculate theoretical minimum radius for perfect circle packing
        bin_area = self.bin_width * self.bin_height
        total_area = num_bins * bin_area
        theoretical_radius = math.sqrt(total_area / math.pi)
        
        # Find absolute minimum radius by iterative reduction
        canvas_radius = center_x
        
        # Start with theoretical minimum and incrementally increase until all images fit
        current_radius = theoretical_radius
        radius_step = 50  # Start with 50-pixel steps
        
        best_placements = None
        best_radius = None
        
        # First, find a working radius
        max_attempts = 100
        attempts = 0
        
        while best_placements is None and attempts < max_attempts:
            test_placements = self._generate_circular_row_placements(
                num_bins, current_radius, center_x, center_y
            )
            
            if len(test_placements) == num_bins:
                best_placements = test_placements
                best_radius = current_radius
                break
            else:
                current_radius += radius_step
                attempts += 1
        
        # Now that we have a working radius, refine it downward
        if best_radius is not None:
            # Binary search for the minimum working radius
            min_radius = theoretical_radius
            max_radius = best_radius
            
            while max_radius - min_radius > 1:
                test_radius = (min_radius + max_radius) / 2
                test_placements = self._generate_circular_row_placements(
                    num_bins, test_radius, center_x, center_y
                )
                
                if len(test_placements) == num_bins:
                    # This radius works, try smaller
                    max_radius = test_radius
                    best_radius = test_radius
                    best_placements = test_placements
                else:
                    # This radius too small, increase minimum
                    min_radius = test_radius
        
        # Calculate final envelope ratio
        if best_radius is not None:
            envelope_area = math.pi * best_radius ** 2
            best_envelope_ratio = envelope_area / total_area
        
        # If no optimal solution found, use fallback with very tight packing
        if best_placements is None:
            canvas_radius = center_x
            working_radius = theoretical_radius * 1.05  # Very tight fallback
            best_placements = self._generate_circular_row_placements(
                num_bins, working_radius, center_x, center_y
            )
            envelope_area = math.pi * working_radius ** 2
            best_envelope_ratio = envelope_area / total_area
            best_radius = working_radius
        
        self.logger.info(f"Circular packing: envelope_ratio={best_envelope_ratio:.2f}, "
                        f"working_radius={best_radius:.1f}")
        
        return best_placements
    
    def _generate_circular_row_placements(self, num_bins: int, working_radius: float,
                                        center_x: int, center_y: int) -> List[Tuple[int, int]]:
        """Generate row-by-row circular placement for given radius."""
        
        placements = []
        images_placed = 0
        
        # Go row by row from top to bottom
        canvas_size = center_x * 2
        current_y = 0
        
        while images_placed < num_bins and current_y + self.bin_height <= canvas_size:
            # Calculate row center Y position
            row_center_y = current_y + self.bin_height // 2
            
            # Calculate distance from canvas center
            y_offset_from_center = abs(row_center_y - center_y)
            
            # Check if this row intersects the working circle
            if y_offset_from_center <= working_radius:
                # Calculate circle width at this Y position using circle equation
                if y_offset_from_center < working_radius:
                    x_half_width = math.sqrt(working_radius**2 - y_offset_from_center**2)
                    row_width = int(2 * x_half_width)
                    
                    # Calculate how many images fit in this row with maximum packing
                    # Use 100% of theoretical capacity for tightest fit
                    theoretical_images = row_width / self.bin_width
                    images_in_row = max(0, int(theoretical_images * 1.0))
                    
                    # Don't exceed remaining images
                    images_in_row = min(images_in_row, num_bins - images_placed)
                    
                    if images_in_row > 0:
                        # Center the row within the available width
                        actual_row_width = images_in_row * self.bin_width
                        row_start_x = center_x - actual_row_width // 2
                        
                        # Place images in this row (left to right)
                        for col in range(images_in_row):
                            x = row_start_x + col * self.bin_width
                            
                            # Ensure within canvas bounds
                            x = max(0, min(x, canvas_size - self.bin_width))
                            y = max(0, min(current_y, canvas_size - self.bin_height))
                            
                            placements.append((x, y))
                            images_placed += 1
                            
                            if images_placed >= num_bins:
                                break
            
            current_y += self.bin_height
            
            # Safety break
            if current_y > canvas_size:
                break
        
        return placements
    
    def _generate_elliptical_constrained_placements(self, num_bins: int, rows: int, cols: int,
                                                  center_x: int, center_y: int, a: float, b: float) -> List[Tuple[int, int]]:
        """Generate elliptical placement that only places bins within ellipse boundary."""
        placements = []
        
        # Calculate grid dimensions
        grid_width = cols * self.bin_width
        grid_height = rows * self.bin_height
        
        # Center the grid
        start_x = center_x - grid_width // 2
        start_y = center_y - grid_height // 2
        
        bins_placed = 0
        
        # Place bins row by row, but only if they fit in ellipse
        for row in range(rows):
            if bins_placed >= num_bins:
                break
                
            for col in range(cols):
                if bins_placed >= num_bins:
                    break
                
                # Calculate bin position
                x = start_x + col * self.bin_width
                y = start_y + row * self.bin_height
                
                # Calculate bin center
                bin_center_x = x + self.bin_width // 2
                bin_center_y = y + self.bin_height // 2
                
                # Check if bin center is within ellipse
                # Ellipse equation: ((x-cx)/a)² + ((y-cy)/b)² ≤ 1
                ellipse_test = ((bin_center_x - center_x) / a) ** 2 + ((bin_center_y - center_y) / b) ** 2
                
                if ellipse_test <= 0.8:  # Use 80% of ellipse for better fit
                    placements.append((x, y))
                    bins_placed += 1
        
        # If we haven't placed all bins, place remaining ones in spiral within ellipse
        if bins_placed < num_bins:
            remaining_placements = self._generate_spiral_placements_elliptical(
                num_bins - bins_placed, center_x, center_y, a * 0.7, b * 0.7, start_index=bins_placed
            )
            placements.extend(remaining_placements)
        
        return placements    
    def _pack_circle_with_binary_search(self, num_bins: int, square_reserve_size: int = 10000) -> PackingResult:
        """
        Pack bins into circle with square reserve using binary envelope search algorithm.
        
        6-step algorithm:
        1. Calculate image area
        2. Create envelope with area same as image area  
        3. Place images, check if any go outside envelope
        4. If outside then increase envelope area
        5. If inside then decrease envelope area
        6. Stop at last area where envelope >= image area
        """
        
        # Step 1: Calculate image area
        image_area = num_bins * self.bin_width * self.bin_height
        self.logger.info(f"Binary search: Image area = {image_area:,} pixels²")
        
        # Step 2: Start with envelope area same as image area
        # For circle: area = π * r², so r = sqrt(area / π)
        min_radius = math.sqrt(image_area / math.pi)
        
        # Set search bounds - max radius includes overhead for inefficiency
        max_radius = math.sqrt(image_area * 3 / math.pi)  # Up to 3x area
        
        self.logger.info(f"Binary search: min_radius={min_radius:.1f}, max_radius={max_radius:.1f}")
        
        best_radius = None
        best_placements = None
        iteration = 0
        
        # Binary search loop
        while max_radius - min_radius > 1.0:  # 1 pixel precision
            iteration += 1
            test_radius = (min_radius + max_radius) / 2
            test_area = math.pi * test_radius * test_radius
            
            self.logger.info(f"Binary search iteration {iteration}: radius={test_radius:.1f}, area={test_area:,.0f}")
            
            # Step 3: Place images and check if any go outside envelope
            placements, all_fit = self._pack_images_in_circle_with_reserve(num_bins, test_radius, square_reserve_size)
            
            if all_fit:
                # Step 5: If inside then decrease envelope area
                self.logger.info(f"  ✓ All {len(placements)} images fit - decreasing envelope area")
                max_radius = test_radius
                best_radius = test_radius
                best_placements = placements
            else:
                # Step 4: If outside then increase envelope area  
                self.logger.info(f"  ✗ Only {len(placements)}/{num_bins} images fit - increasing envelope area")
                min_radius = test_radius
        
        # Step 6: Stop at last area where envelope is larger than image area
        if best_radius is None:
            # Use the minimum working radius
            best_radius = max_radius
            best_placements, _ = self._pack_images_in_circle_with_reserve(num_bins, best_radius, square_reserve_size)
        
        final_canvas_size = int(2 * best_radius)
        final_envelope_area = math.pi * best_radius * best_radius
        efficiency = image_area / final_envelope_area * 100
        
        self.logger.info(f"Binary search complete: radius={best_radius:.1f}, efficiency={efficiency:.1f}%")
        
        # Calculate grid dimensions for compatibility
        rows = int(final_canvas_size / self.bin_height)
        cols = int(final_canvas_size / self.bin_width)
        
        return PackingResult(
            rows=rows,
            columns=cols,
            canvas_width=final_canvas_size,
            canvas_height=final_canvas_size,
            placements=best_placements,
            envelope_shape=EnvelopeShape.CIRCLE_WITH_SQUARE_RESERVE,
            total_bins=num_bins,
            bin_width=self.bin_width,
            bin_height=self.bin_height
        )
    
    def _pack_images_in_circle_with_reserve(self, num_bins: int, circle_radius: float, square_reserve_size: int):
        """
        Pack images row-by-row in circle with square reserve.
        Returns: (placements, all_images_fit)
        """
        canvas_size = int(2 * circle_radius)
        center_x = center_y = canvas_size // 2
        
        placements = []
        images_placed = 0
        
        # Go row by row from top to bottom
        current_y = 0
        
        while images_placed < num_bins and current_y + self.bin_height <= canvas_size:
            # Place images left to right in this row
            current_x = 0
            
            while images_placed < num_bins and current_x + self.bin_width <= canvas_size:
                # Check if this position is valid
                if self._is_position_inside_circle_and_outside_square(current_x, current_y, circle_radius, center_x, center_y, square_reserve_size):
                    placements.append((current_x, current_y))
                    images_placed += 1
                
                current_x += self.bin_width
            
            current_y += self.bin_height
        
        # Check if all images fit
        all_images_fit = (images_placed == num_bins)
        return placements, all_images_fit
    
    def _is_position_inside_circle_and_outside_square(self, x: int, y: int, circle_radius: float, 
                                                    center_x: int, center_y: int, square_reserve_size: int) -> bool:
        """Check if position is inside circle and outside square reserve."""
        # Check if tile center is inside circle
        tile_center_x = x + self.bin_width // 2
        tile_center_y = y + self.bin_height // 2
        distance_from_center = math.sqrt((tile_center_x - center_x)**2 + (tile_center_y - center_y)**2)
        
        if distance_from_center > circle_radius:
            return False  # Outside circle
        
        # Check if tile overlaps with center square reserve
        square_half_size = square_reserve_size // 2
        square_left = center_x - square_half_size
        square_right = center_x + square_half_size
        square_top = center_y - square_half_size
        square_bottom = center_y + square_half_size
        
        # Tile bounds
        tile_left = x
        tile_right = x + self.bin_width
        tile_top = y
        tile_bottom = y + self.bin_height
        
        # Check if tile overlaps with square reserve
        if not (tile_right <= square_left or tile_left >= square_right or 
                tile_bottom <= square_top or tile_top >= square_bottom):
            return False  # Overlaps with square reserve
        
        return True
