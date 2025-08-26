"""
GUI for NanoFiche Image Prep Windows Application.
Provides all required prompts and workflow management.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import threading
import logging
from typing import List, Optional
from PIL import Image
import os

from .packer import NanoFichePacker, EnvelopeShape, EnvelopeSpec, PackingResult
from .renderer import NanoFicheRenderer
from .image_bin import ImageBin
from .logger import setup_logging, generate_log_filename, generate_tiff_filename


class NanoFicheGUI:
    """Main GUI application for NanoFiche Image Prep."""
    
    def __init__(self, root: tk.Tk):
        """Initialize the GUI application."""
        self.root = root
        self.root.title("NanoFiche Image Prep")
        self.root.geometry("800x600")
        
        # Setup logging
        setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.packer = None
        self.renderer = NanoFicheRenderer()
        self.image_bins: List[ImageBin] = []
        self.packing_result: Optional[PackingResult] = None
        self.preview_path: Optional[Path] = None
        
        # Create GUI
        self._create_widgets()
        self._setup_layout()
        
        self.logger.info("NanoFiche Image Prep GUI initialized")
    
    def _create_widgets(self):
        """Create all GUI widgets."""
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        row = 0
        
        # 1. Project Name
        ttk.Label(main_frame, text="Project Name:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.project_name_var = tk.StringVar(value="nanofiche_project")
        self.project_name_entry = ttk.Entry(main_frame, textvariable=self.project_name_var, width=40)
        self.project_name_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=2)
        row += 1
        
        # 2. Bin Dimensions
        ttk.Label(main_frame, text="Bin Dimensions (a x b):").grid(row=row, column=0, sticky=tk.W, pady=2)
        bin_frame = ttk.Frame(main_frame)
        bin_frame.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=2)
        
        self.bin_width_var = tk.StringVar(value="1800")
        self.bin_height_var = tk.StringVar(value="2300")
        
        ttk.Label(bin_frame, text="Width:").pack(side=tk.LEFT)
        ttk.Entry(bin_frame, textvariable=self.bin_width_var, width=10).pack(side=tk.LEFT, padx=2)
        ttk.Label(bin_frame, text="Height:").pack(side=tk.LEFT, padx=(10, 0))
        ttk.Entry(bin_frame, textvariable=self.bin_height_var, width=10).pack(side=tk.LEFT, padx=2)
        ttk.Label(bin_frame, text="pixels").pack(side=tk.LEFT, padx=(5, 0))
        row += 1
        
        # 3. Envelope Shape
        ttk.Label(main_frame, text="Envelope Shape:").grid(row=row, column=0, sticky=tk.W, pady=2)
        envelope_frame = ttk.Frame(main_frame)
        envelope_frame.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=2)
        
        self.envelope_shape_var = tk.StringVar(value="rectangle")
        shape_combo = ttk.Combobox(envelope_frame, textvariable=self.envelope_shape_var, 
                                   values=["square", "rectangle", "circle", "ellipse"], 
                                   state="readonly", width=15)
        shape_combo.pack(side=tk.LEFT)
        shape_combo.bind('<<ComboboxSelected>>', self._on_shape_change)
        
        # Aspect ratio inputs (for rectangle and ellipse)
        self.aspect_frame = ttk.Frame(envelope_frame)
        self.aspect_frame.pack(side=tk.LEFT, padx=(10, 0))
        
        ttk.Label(self.aspect_frame, text="Aspect (x:y):").pack(side=tk.LEFT)
        self.aspect_x_var = tk.StringVar(value="1.29")
        self.aspect_y_var = tk.StringVar(value="1.0")
        
        ttk.Entry(self.aspect_frame, textvariable=self.aspect_x_var, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Label(self.aspect_frame, text=":").pack(side=tk.LEFT)
        ttk.Entry(self.aspect_frame, textvariable=self.aspect_y_var, width=8).pack(side=tk.LEFT, padx=2)
        row += 1
        
        # 4. Reserved Space Options
        ttk.Label(main_frame, text="Reserved Space:").grid(row=row, column=0, sticky=tk.W, pady=2)
        reserve_frame = ttk.Frame(main_frame)
        reserve_frame.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=2)
        
        self.reserve_enabled_var = tk.BooleanVar(value=False)
        self.reserve_checkbox = ttk.Checkbutton(reserve_frame, text="Enable", 
                                                variable=self.reserve_enabled_var,
                                                command=self._toggle_reserve_options)
        self.reserve_checkbox.pack(side=tk.LEFT)
        
        # Reserve dimensions
        self.reserve_dims_frame = ttk.Frame(reserve_frame)
        self.reserve_dims_frame.pack(side=tk.LEFT, padx=(10, 0))
        
        ttk.Label(self.reserve_dims_frame, text="Size:").pack(side=tk.LEFT)
        self.reserve_width_var = tk.StringVar(value="5000")
        self.reserve_height_var = tk.StringVar(value="5000")
        
        self.reserve_width_entry = ttk.Entry(self.reserve_dims_frame, textvariable=self.reserve_width_var, width=8)
        self.reserve_width_entry.pack(side=tk.LEFT, padx=2)
        ttk.Label(self.reserve_dims_frame, text="x").pack(side=tk.LEFT)
        self.reserve_height_entry = ttk.Entry(self.reserve_dims_frame, textvariable=self.reserve_height_var, width=8)
        self.reserve_height_entry.pack(side=tk.LEFT, padx=2)
        ttk.Label(self.reserve_dims_frame, text="pixels").pack(side=tk.LEFT, padx=(2, 10))
        
        # Reserve position
        ttk.Label(self.reserve_dims_frame, text="Position:").pack(side=tk.LEFT)
        self.reserve_position_var = tk.StringVar(value="top-left")
        self.reserve_position_menu = ttk.Combobox(self.reserve_dims_frame, 
                                                  textvariable=self.reserve_position_var,
                                                  values=["center", "top-left"],
                                                  width=10,
                                                  state="readonly")
        self.reserve_position_menu.pack(side=tk.LEFT, padx=2)
        
        # Auto-optimize checkbox
        self.reserve_auto_var = tk.BooleanVar(value=True)
        self.reserve_auto_checkbox = ttk.Checkbutton(self.reserve_dims_frame, 
                                                     text="Auto-optimize",
                                                     variable=self.reserve_auto_var,
                                                     command=self._toggle_auto_optimize)
        self.reserve_auto_checkbox.pack(side=tk.LEFT, padx=(10, 0))
        
        # Initially disable reserve options
        self._toggle_reserve_options()
        row += 1
        
        # 5. Folder Location
        ttk.Label(main_frame, text="Raster Folder:").grid(row=row, column=0, sticky=tk.W, pady=2)
        folder_frame = ttk.Frame(main_frame)
        folder_frame.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=2)
        folder_frame.columnconfigure(0, weight=1)
        
        self.folder_path_var = tk.StringVar()
        self.folder_entry = ttk.Entry(folder_frame, textvariable=self.folder_path_var)
        self.folder_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(folder_frame, text="Browse...", command=self._browse_folder).grid(row=0, column=1)
        row += 1
        
        # 5. Output Location
        ttk.Label(main_frame, text="Output Location:").grid(row=row, column=0, sticky=tk.W, pady=2)
        output_frame = ttk.Frame(main_frame)
        output_frame.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=2)
        output_frame.columnconfigure(0, weight=1)
        
        self.output_path_var = tk.StringVar()
        self.output_entry = ttk.Entry(output_frame, textvariable=self.output_path_var)
        self.output_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(output_frame, text="Browse...", command=self._browse_output).grid(row=0, column=1)
        row += 1
        
        # File info display
        ttk.Separator(main_frame, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        ttk.Label(main_frame, text="File Information:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.file_info_var = tk.StringVar(value="No folder selected")
        self.file_info_label = ttk.Label(main_frame, textvariable=self.file_info_var, foreground="blue")
        self.file_info_label.grid(row=row, column=1, sticky=tk.W, pady=2)
        row += 1
        
        # Packing info display
        ttk.Label(main_frame, text="Packing Result:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.packing_info_var = tk.StringVar(value="Not calculated")
        self.packing_info_label = ttk.Label(main_frame, textvariable=self.packing_info_var, foreground="green")
        self.packing_info_label.grid(row=row, column=1, sticky=tk.W, pady=2)
        row += 1
        
        # Buttons
        ttk.Separator(main_frame, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row, column=0, columnspan=2, pady=10)
        
        self.validate_button = ttk.Button(button_frame, text="Validate & Calculate", command=self._validate_and_calculate)
        self.validate_button.pack(side=tk.LEFT, padx=5)
        
        self.preview_button = ttk.Button(button_frame, text="Generate Preview", command=self._generate_preview, state=tk.DISABLED)
        self.preview_button.pack(side=tk.LEFT, padx=5)
        
        self.approve_button = ttk.Button(button_frame, text="Approve & Generate Full TIFF", command=self._approve_layout, state=tk.DISABLED)
        self.approve_button.pack(side=tk.LEFT, padx=5)
        
        self.reject_button = ttk.Button(button_frame, text="Reject & Generate Thumbnail", command=self._reject_layout, state=tk.DISABLED)
        self.reject_button.pack(side=tk.LEFT, padx=5)
        row += 1
        
        # Progress bar
        self.progress_var = tk.StringVar(value="Ready")
        ttk.Label(main_frame, textvariable=self.progress_var).grid(row=row, column=0, columnspan=2, pady=5)
        row += 1
        
        self.progress_bar = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress_bar.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Initialize shape change
        self._on_shape_change()
    
    def _setup_layout(self):
        """Setup additional layout configuration."""
        pass
    
    def _on_shape_change(self, event=None):
        """Handle envelope shape selection change."""
        shape = self.envelope_shape_var.get()
        
        if shape in ["rectangle", "ellipse"]:
            # Show aspect ratio inputs
            for widget in self.aspect_frame.winfo_children():
                widget.pack(side=tk.LEFT)
        else:
            # Hide aspect ratio inputs
            for widget in self.aspect_frame.winfo_children():
                widget.pack_forget()
    
    def _toggle_reserve_options(self):
        """Enable/disable reserve dimension inputs based on checkbox."""
        if self.reserve_enabled_var.get():
            state = "normal"
            menu_state = "readonly"
        else:
            state = "disabled"
            menu_state = "disabled"
        
        self.reserve_width_entry.config(state=state)
        self.reserve_height_entry.config(state=state)
        self.reserve_position_menu.config(state=menu_state)
        self.reserve_auto_checkbox.config(state="normal" if self.reserve_enabled_var.get() else "disabled")
        
        # Trigger auto-optimize toggle
        self._toggle_auto_optimize()
    
    def _toggle_auto_optimize(self):
        """Enable/disable manual size inputs based on auto-optimize."""
        if self.reserve_enabled_var.get() and self.reserve_auto_var.get():
            # Disable manual size inputs when auto-optimize is on
            self.reserve_width_entry.config(state="disabled")
            self.reserve_height_entry.config(state="disabled")
            # Force top-left position for optimization
            self.reserve_position_var.set("top-left")
            self.reserve_position_menu.config(state="disabled")
        elif self.reserve_enabled_var.get():
            # Enable manual inputs when auto-optimize is off
            self.reserve_width_entry.config(state="normal")
            self.reserve_height_entry.config(state="normal")
            self.reserve_position_menu.config(state="readonly")
    
    def _browse_folder(self):
        """Browse for raster folder."""
        folder = filedialog.askdirectory(title="Select Raster Image Folder")
        if folder:
            self.folder_path_var.set(folder)
            self._analyze_folder()
    
    def _browse_output(self):
        """Browse for output location."""
        folder = filedialog.askdirectory(title="Select Output Location")
        if folder:
            self.output_path_var.set(folder)
    
    def _analyze_folder(self):
        """Analyze selected folder for raster files."""
        folder_path = Path(self.folder_path_var.get())
        
        if not folder_path.exists():
            self.file_info_var.set("Folder does not exist")
            return
        
        try:
            # Find all image files
            image_extensions = {'.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp'}
            image_files = []
            
            for file_path in folder_path.iterdir():
                if file_path.is_file() and file_path.suffix.lower() in image_extensions:
                    image_files.append(file_path)
            
            # Sort by filename
            image_files.sort()
            
            if not image_files:
                self.file_info_var.set("No image files found")
                return
            
            self.file_info_var.set(f"Found {len(image_files)} image files")
            self.logger.info(f"Found {len(image_files)} image files in {folder_path}")
            
        except Exception as e:
            self.file_info_var.set(f"Error analyzing folder: {e}")
            self.logger.error(f"Error analyzing folder: {e}")
    
    def _validate_and_calculate(self):
        """Validate inputs and calculate optimal packing."""
        try:
            # Validate inputs
            project_name = self.project_name_var.get().strip()
            if not project_name:
                messagebox.showerror("Error", "Please enter a project name")
                return
            
            try:
                bin_width = int(self.bin_width_var.get())
                bin_height = int(self.bin_height_var.get())
            except ValueError:
                messagebox.showerror("Error", "Bin dimensions must be integers")
                return
            
            if bin_width <= 0 or bin_height <= 0:
                messagebox.showerror("Error", "Bin dimensions must be positive")
                return
            
            folder_path = Path(self.folder_path_var.get())
            if not folder_path.exists():
                messagebox.showerror("Error", "Please select a valid raster folder")
                return
            
            output_path = Path(self.output_path_var.get())
            if not output_path.exists():
                messagebox.showerror("Error", "Please select a valid output location")
                return
            
            # Get envelope specification
            envelope_spec = self._get_envelope_spec()
            
            # Start validation in thread
            self._start_progress("Validating images and calculating layout...")
            threading.Thread(target=self._validate_worker, 
                           args=(bin_width, bin_height, folder_path, envelope_spec), 
                           daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Validation error: {e}")
            self.logger.error(f"Validation error: {e}")
    
    def _validate_worker(self, bin_width: int, bin_height: int, folder_path: Path, envelope_spec: EnvelopeSpec):
        """Worker thread for validation and calculation."""
        try:
            # Find and validate image files
            image_extensions = {'.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp'}
            image_files = []
            
            for file_path in folder_path.iterdir():
                if file_path.is_file() and file_path.suffix.lower() in image_extensions:
                    image_files.append(file_path)
            
            # Sort files numerically by extracting numbers from filename
            import re
            def natural_sort_key(path):
                """Extract numeric part from filename for proper sorting."""
                filename = path.name
                # Look for numbers in filename
                numbers = re.findall(r'\d+', filename)
                if numbers:
                    # Use the last number found (most specific)
                    return int(numbers[-1])
                return 0
            
            image_files.sort(key=natural_sort_key)
            
            if not image_files:
                self.root.after(0, lambda: self._validation_complete("No image files found", None, None))
                return
            
            # Validate image dimensions
            self.image_bins = []
            oversized_files = []
            
            for i, file_path in enumerate(image_files):
                try:
                    with Image.open(file_path) as img:
                        width, height = img.size
                        
                        if width > bin_width or height > bin_height:
                            oversized_files.append(f"{file_path.name} ({width}x{height})")
                        else:
                            self.image_bins.append(ImageBin(file_path, bin_width, bin_height, i))
                            
                except Exception as e:
                    self.logger.warning(f"Could not read {file_path}: {e}")
                    continue
            
            if oversized_files:
                error_msg = f"The following files exceed bin dimensions ({bin_width}x{bin_height}):\n"
                error_msg += "\n".join(oversized_files[:10])  # Show first 10
                if len(oversized_files) > 10:
                    error_msg += f"\n... and {len(oversized_files) - 10} more"
                
                self.root.after(0, lambda: self._validation_complete(error_msg, None, None))
                return
            
            if not self.image_bins:
                self.root.after(0, lambda: self._validation_complete("No valid images found", None, None))
                return
            
            # Calculate optimal packing
            self.packer = NanoFichePacker(bin_width, bin_height)
            packing_result = self.packer.pack(len(self.image_bins), envelope_spec)
            
            result_text = f"Grid: {packing_result.rows}x{packing_result.columns}, "
            result_text += f"Canvas: {packing_result.canvas_width}x{packing_result.canvas_height} pixels"
            
            self.root.after(0, lambda: self._validation_complete("Validation successful", result_text, packing_result))
            
        except Exception as e:
            self.root.after(0, lambda: self._validation_complete(f"Error: {e}", None, None))
    
    def _validation_complete(self, message: str, result_text: Optional[str], packing_result: Optional[PackingResult]):
        """Handle validation completion."""
        self._stop_progress()
        
        if packing_result is None:
            messagebox.showerror("Validation Failed", message)
            self.packing_info_var.set("Validation failed")
        else:
            self.packing_result = packing_result
            self.packing_info_var.set(result_text)
            self.preview_button.config(state=tk.NORMAL)
            messagebox.showinfo("Validation Complete", 
                              f"{message}\n\nFiles: {len(self.image_bins)}\n{result_text}")
    
    def _get_envelope_spec(self) -> EnvelopeSpec:
        """Get envelope specification from GUI inputs."""
        shape_str = self.envelope_shape_var.get()
        shape = EnvelopeShape(shape_str)
        
        if shape in [EnvelopeShape.RECTANGLE, EnvelopeShape.ELLIPSE]:
            try:
                aspect_x = float(self.aspect_x_var.get())
                aspect_y = float(self.aspect_y_var.get())
            except ValueError:
                aspect_x = aspect_y = 1.0
        else:
            aspect_x = aspect_y = 1.0
        
        # Get reserved space settings
        reserve_enabled = self.reserve_enabled_var.get()
        try:
            reserve_width = int(self.reserve_width_var.get()) if reserve_enabled else 5000
            reserve_height = int(self.reserve_height_var.get()) if reserve_enabled else 5000
        except (ValueError, AttributeError):
            reserve_width = reserve_height = 5000
        
        reserve_position = self.reserve_position_var.get() if reserve_enabled else "center"
        reserve_auto_size = self.reserve_auto_var.get() if reserve_enabled else False
        
        return EnvelopeSpec(
            shape=shape,
            aspect_x=aspect_x,
            aspect_y=aspect_y,
            reserve_enabled=reserve_enabled,
            reserve_width=reserve_width,
            reserve_height=reserve_height,
            reserve_position=reserve_position,
            reserve_auto_size=reserve_auto_size
        )
    
    def _generate_preview(self):
        """Generate preview TIFF."""
        if not self.packing_result or not self.image_bins:
            messagebox.showerror("Error", "Please validate and calculate first")
            return
        
        try:
            output_path = Path(self.output_path_var.get())
            project_name = self.project_name_var.get().strip()
            
            preview_filename = f"{project_name}_preview.tif"
            self.preview_path = output_path / preview_filename
            
            self._start_progress("Generating preview...")
            threading.Thread(target=self._preview_worker, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Preview generation error: {e}")
    
    def _preview_worker(self):
        """Worker thread for preview generation."""
        try:
            self.renderer.generate_preview(
                self.image_bins,
                self.packing_result,
                self.preview_path
            )
            
            self.root.after(0, self._preview_complete)
            
        except Exception as e:
            self.root.after(0, lambda: self._preview_error(str(e)))
    
    def _preview_complete(self):
        """Handle preview generation completion."""
        self._stop_progress()
        self.approve_button.config(state=tk.NORMAL)
        self.reject_button.config(state=tk.NORMAL)
        
        messagebox.showinfo("Preview Complete", 
                          f"Preview saved: {self.preview_path}\n\nPlease review and approve or reject the layout.")
    
    def _preview_error(self, error: str):
        """Handle preview generation error."""
        self._stop_progress()
        messagebox.showerror("Preview Error", f"Failed to generate preview: {error}")
    
    def _approve_layout(self):
        """Approve layout and generate full TIFF."""
        result = messagebox.askyesno("Approve Layout", 
                                    "Generate full resolution TIFF?\n\nThis may take several minutes for large layouts.")
        if result:
            self._generate_final_tiff(approved=True)
    
    def _reject_layout(self):
        """Reject layout and generate thumbnail."""
        result = messagebox.askyesno("Reject Layout", 
                                    "Generate thumbnail TIFF instead?")
        if result:
            self._generate_final_tiff(approved=False)
    
    def _generate_final_tiff(self, approved: bool):
        """Generate final TIFF (full or thumbnail)."""
        try:
            output_path = Path(self.output_path_var.get())
            project_name = self.project_name_var.get().strip()
            
            tiff_filename = generate_tiff_filename(project_name, approved)
            log_filename = generate_log_filename(project_name, approved)
            
            tiff_path = output_path / tiff_filename
            log_path = output_path / log_filename
            
            action = "full TIFF" if approved else "thumbnail"
            self._start_progress(f"Generating {action}...")
            
            threading.Thread(target=self._final_tiff_worker, 
                           args=(tiff_path, log_path, project_name, approved), 
                           daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Final TIFF generation error: {e}")
    
    def _final_tiff_worker(self, tiff_path: Path, log_path: Path, project_name: str, approved: bool):
        """Worker thread for final TIFF generation."""
        try:
            if approved:
                self.renderer.generate_full_tiff(
                    self.image_bins,
                    self.packing_result,
                    tiff_path,
                    log_path,
                    project_name,
                    approved=True
                )
            else:
                self.renderer.generate_thumbnail_tiff(
                    self.image_bins,
                    self.packing_result,
                    tiff_path,
                    log_path,
                    project_name,
                    approved=False
                )
            
            self.root.after(0, lambda: self._final_tiff_complete(tiff_path, log_path, approved))
            
        except Exception as e:
            self.root.after(0, lambda: self._final_tiff_error(str(e)))
    
    def _final_tiff_complete(self, tiff_path: Path, log_path: Path, approved: bool):
        """Handle final TIFF generation completion."""
        self._stop_progress()
        
        action = "Full TIFF" if approved else "Thumbnail TIFF"
        messagebox.showinfo(f"{action} Complete", 
                          f"{action} generated successfully!\n\nOutput: {tiff_path}\nLog: {log_path}")
        
        # Reset buttons for next project
        self.preview_button.config(state=tk.DISABLED)
        self.approve_button.config(state=tk.DISABLED)
        self.reject_button.config(state=tk.DISABLED)
    
    def _final_tiff_error(self, error: str):
        """Handle final TIFF generation error."""
        self._stop_progress()
        messagebox.showerror("Generation Error", f"Failed to generate final TIFF: {error}")
    
    def _start_progress(self, message: str):
        """Start progress indication."""
        self.progress_var.set(message)
        self.progress_bar.start()
        self.validate_button.config(state=tk.DISABLED)
    
    def _stop_progress(self):
        """Stop progress indication."""
        self.progress_bar.stop()
        self.progress_var.set("Ready")
        self.validate_button.config(state=tk.NORMAL)