import customtkinter as ctk
from tkinter import filedialog, messagebox
import tkinter as tk
from tkinterdnd2 import DND_FILES, TkinterDnD
from typing import List, Optional
import threading
from pathlib import Path
from datetime import datetime
import pandas as pd

from config import (
    APP_NAME, APP_VERSION, APP_AUTHOR, APP_DESCRIPTION,
    WINDOW_SIZE, WINDOW_MIN_SIZE, THEME_MODE, COLOR_THEME,
    CSV_DELIMITERS, ENCODING_OPTIONS, PREVIEW_ROWS, COLORS, BASE_DIR
)
from csv_merger import CSVExcelMerger
from csv_splitter import CSVExcelSplitter
from utils import RecentFilesManager, logger, DataFrameHelper


class CSVExcelManagerGUI:
    """Main Application GUI with CustomTkinter"""

    def __init__(self):
        # Set theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Create main window with drag-drop support
        self.root = TkinterDnD.Tk()
        self.root.title(f"{APP_NAME} v{APP_VERSION} - By {APP_AUTHOR}")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 700)
        self.root.configure(bg="#1a1a1a")

        # Configure grid weight for responsive design
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Set icon if exists
        icon_path = BASE_DIR / "icon.ico"
        if not icon_path.exists():
            icon_path = BASE_DIR / "Icon.ico"
        if icon_path.exists():
            self.root.iconbitmap(str(icon_path))

        # Initialize managers
        self.merger = CSVExcelMerger()
        self.splitter = CSVExcelSplitter()
        self.recent_files_manager = RecentFilesManager()

        # Setup UI
        self.setup_ui()
        self.apply_custom_styles()

    def apply_custom_styles(self):
        """Apply custom styling to the tabview"""
        # Style the tab buttons with lemon-lime active color and spacing
        self.tabview._segmented_button.configure(
            height=50,
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            fg_color="#0a0a0a",
            selected_color=COLORS['button'],
            selected_hover_color=COLORS['button_hover'],
            unselected_color="#2b2b2b",
            unselected_hover_color="#3b3b3b",
            text_color=COLORS['text'],
            border_width=0,
            corner_radius=10
        )

        # Add spacing between tab buttons
        try:
            # Set spacing between buttons (gap between tabs)
            self.tabview._segmented_button._spacing = 20  # Increased spacing
        except Exception as e:
            logger.error(f"Error setting tab spacing: {e}")

        # Update text colors for better visibility
        self.update_tab_colors()

    def update_tab_colors(self):
        """Update tab text colors - dark for active tab, white for inactive"""
        try:
            current_tab = self.tabview.get()
            # Access the segmented button's internal buttons
            segmented_button = self.tabview._segmented_button

            # Update colors for each tab
            for tab_name in ["Merge Files", "Split File"]:
                if tab_name == current_tab:
                    # Active tab: dark text on lemon-lime background
                    segmented_button._buttons_dict[tab_name].configure(
                        text_color="#000000",  # Black text for active tab
                        text_color_disabled="#000000"
                    )
                else:
                    # Inactive tab: white text
                    segmented_button._buttons_dict[tab_name].configure(
                        text_color=COLORS['text'],  # White text for inactive tab
                        text_color_disabled=COLORS['text']
                    )

            # Update dropdown colors based on active tab
            self.update_dropdown_colors(current_tab)
        except Exception as e:
            logger.error(f"Error updating tab colors: {e}")

    def update_dropdown_colors(self, active_tab):
        """Update dropdown menu colors based on active tab"""
        try:
            # Define dropdown widgets for each tab
            merge_dropdowns = [self.merge_encoding, self.merge_delimiter]
            split_dropdowns = [self.split_encoding, self.split_delimiter, self.split_output_format]

            if active_tab == "Merge Files":
                # Merge tab is active - lemon-lime dropdowns with dark text
                for dropdown in merge_dropdowns:
                    dropdown.configure(
                        button_color=COLORS['button'],
                        button_hover_color=COLORS['button_hover'],
                        dropdown_hover_color=COLORS['button'],
                        dropdown_text_color="#000000",  # Dark text in dropdown menu
                        text_color="#000000"  # Dark text on button
                    )
                # Split tab is inactive - muted dropdowns
                for dropdown in split_dropdowns:
                    dropdown.configure(
                        button_color="#3a3a3a",
                        button_hover_color="#4a4a4a",
                        dropdown_hover_color="#3a3a3a",
                        dropdown_text_color=COLORS['text'],  # White text in dropdown menu
                        text_color=COLORS['text']  # White text on button
                    )
            else:  # "Split File" tab is active
                # Split tab is active - lemon-lime dropdowns with dark text
                for dropdown in split_dropdowns:
                    dropdown.configure(
                        button_color=COLORS['button'],
                        button_hover_color=COLORS['button_hover'],
                        dropdown_hover_color=COLORS['button'],
                        dropdown_text_color="#000000",  # Dark text in dropdown menu
                        text_color="#000000"  # Dark text on button
                    )
                # Merge tab is inactive - muted dropdowns
                for dropdown in merge_dropdowns:
                    dropdown.configure(
                        button_color="#3a3a3a",
                        button_hover_color="#4a4a4a",
                        dropdown_hover_color="#3a3a3a",
                        dropdown_text_color=COLORS['text'],  # White text in dropdown menu
                        text_color=COLORS['text']  # White text on button
                    )
        except Exception as e:
            logger.error(f"Error updating dropdown colors: {e}")

    def on_tab_change(self):
        """Called when tab is changed - updates text colors"""
        self.update_tab_colors()

    def setup_ui(self):
        """Setup main UI components"""
        # Main container - remove borders
        main_container = ctk.CTkFrame(self.root, fg_color="#1a1a1a", border_width=0)
        main_container.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        main_container.grid_rowconfigure(0, weight=1)
        main_container.grid_columnconfigure(0, weight=1)

        # Create tabview with command callback for tab color updates
        self.tabview = ctk.CTkTabview(
            main_container,
            fg_color="#1a1a1a",
            border_width=0,
            command=self.on_tab_change
        )
        self.tabview.grid(row=0, column=0, sticky="nsew")

        # Add tabs (NO EMOJIS)
        self.merge_tab = self.tabview.add("Merge Files")
        self.split_tab = self.tabview.add("Split File")

        # Configure tabs to be responsive
        self.merge_tab.grid_rowconfigure(0, weight=1)
        self.merge_tab.grid_columnconfigure(0, weight=1)
        self.merge_tab.grid_columnconfigure(1, weight=2)

        self.split_tab.grid_rowconfigure(0, weight=1)
        self.split_tab.grid_columnconfigure(0, weight=1)
        self.split_tab.grid_columnconfigure(1, weight=2)

        # Setup each tab
        self.setup_merge_tab()
        self.setup_split_tab()

    def setup_merge_tab(self):
        """Setup Merge Files tab with responsive design"""
        # Left panel (controls) - takes 1/3 of space
        left_panel = ctk.CTkScrollableFrame(
            self.merge_tab,
            fg_color="transparent",
            border_width=0
        )
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        # Right panel (preview) - takes 2/3 of space
        right_panel = ctk.CTkFrame(self.merge_tab, fg_color="#0a0a0a", border_width=0)
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        right_panel.grid_rowconfigure(1, weight=1)
        right_panel.grid_columnconfigure(0, weight=1)

        # === LEFT PANEL CONTENT ===
        # Title
        title = ctk.CTkLabel(
            left_panel,
            text="Merge Multiple Files",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color=COLORS['text']
        )
        title.pack(pady=(5, 15))

        # Drag & Drop area
        drop_frame = ctk.CTkFrame(
            left_panel,
            fg_color=COLORS['bg_dark'],
            border_width=1,
            border_color="#3a3a3a"
        )
        drop_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.merge_placeholder = ctk.CTkLabel(
            drop_frame,
            text="📁 Drag & Drop files here",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color="gray"
        )
        self.merge_placeholder.pack(pady=10)

        # File listbox
        list_frame = ctk.CTkFrame(drop_frame, fg_color="transparent", border_width=0)
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.merge_file_listbox = tk.Listbox(
            list_frame,
            height=10,
            bg="#2b2b2b",
            fg="white",
            selectbackground=COLORS['button'],
            selectforeground="black",
            font=("Segoe UI", 10),
            borderwidth=0,
            highlightthickness=0
        )
        self.merge_file_listbox.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(list_frame, command=self.merge_file_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.merge_file_listbox.config(yscrollcommand=scrollbar.set)

        # Enable drag and drop
        drop_frame.drop_target_register(DND_FILES)
        drop_frame.dnd_bind('<<Drop>>', self.on_merge_drop)

        # File buttons
        btn_frame = ctk.CTkFrame(left_panel, fg_color="transparent", border_width=0)
        btn_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkButton(
            btn_frame,
            text="Add Files",
            command=self.add_merge_files,
            height=50,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color=COLORS['button'],
            hover_color=COLORS['button_hover'],
            text_color="black",
            border_width=0
        ).pack(side="left", expand=True, padx=2)

        ctk.CTkButton(
            btn_frame,
            text="Remove",
            command=self.remove_merge_file,
            height=50,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color=COLORS['button'],
            hover_color=COLORS['button_hover'],
            text_color="black",
            border_width=0
        ).pack(side="left", expand=True, padx=2)

        ctk.CTkButton(
            btn_frame,
            text="Clear All",
            command=self.clear_merge_files,
            height=50,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color=COLORS['button'],
            hover_color=COLORS['button_hover'],
            text_color="black",
            border_width=0
        ).pack(side="left", expand=True, padx=2)

        # Options
        options_frame = ctk.CTkFrame(left_panel, fg_color="transparent", border_width=0)
        options_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(
            options_frame,
            text="Options:",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=COLORS['text']
        ).pack(anchor="w", pady=3)

        self.merge_keep_header = ctk.CTkSwitch(
            options_frame,
            text="Keep Headers",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLORS['text'],
            progress_color=COLORS['toggle_active'],
            button_color="gray",
            button_hover_color=COLORS['toggle_active']
        )
        self.merge_keep_header.pack(anchor="w", pady=2)
        self.merge_keep_header.select()

        self.merge_skip_empty = ctk.CTkSwitch(
            options_frame,
            text="Skip Empty Rows",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLORS['text'],
            progress_color=COLORS['toggle_active'],
            button_color="gray",
            button_hover_color=COLORS['toggle_active']
        )
        self.merge_skip_empty.pack(anchor="w", pady=2)
        self.merge_skip_empty.select()

        self.merge_remove_duplicates = ctk.CTkSwitch(
            options_frame,
            text="Remove Duplicates",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLORS['text'],
            progress_color=COLORS['toggle_active'],
            button_color="gray",
            button_hover_color=COLORS['toggle_active']
        )
        self.merge_remove_duplicates.pack(anchor="w", pady=2)

        # Encoding & Delimiter
        settings_frame = ctk.CTkFrame(left_panel, fg_color="transparent", border_width=0)
        settings_frame.pack(fill="x", padx=5, pady=5)

        enc_frame = ctk.CTkFrame(settings_frame, fg_color="transparent", border_width=0)
        enc_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(
            enc_frame,
            text="Encoding:",
            text_color=COLORS['text'],
            width=80,
            font=ctk.CTkFont(family="Segoe UI", size=11)
        ).pack(side="left", padx=2)
        self.merge_encoding = ctk.CTkComboBox(
            enc_frame,
            values=ENCODING_OPTIONS,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            button_color=COLORS['button'],
            button_hover_color=COLORS['button_hover'],
            border_width=0,
            dropdown_hover_color=COLORS['button'],
            text_color="#000000",  # Dark text on button
            dropdown_text_color="#000000"  # Dark text in dropdown menu
        )
        self.merge_encoding.set('utf-8')
        self.merge_encoding.pack(side="left", fill="x", expand=True, padx=2)

        delim_frame = ctk.CTkFrame(settings_frame, fg_color="transparent", border_width=0)
        delim_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(
            delim_frame,
            text="Delimiter:",
            text_color=COLORS['text'],
            width=80,
            font=ctk.CTkFont(family="Segoe UI", size=11)
        ).pack(side="left", padx=2)
        self.merge_delimiter = ctk.CTkComboBox(
            delim_frame,
            values=list(CSV_DELIMITERS.keys()),
            font=ctk.CTkFont(family="Segoe UI", size=11),
            button_color=COLORS['button'],
            button_hover_color=COLORS['button_hover'],
            border_width=0,
            dropdown_hover_color=COLORS['button'],
            text_color="#000000",  # Dark text on button
            dropdown_text_color="#000000"  # Dark text in dropdown menu
        )
        self.merge_delimiter.set('Comma (,)')
        self.merge_delimiter.pack(side="left", fill="x", expand=True, padx=2)

        # Progress
        self.merge_progress = ctk.CTkProgressBar(
            left_panel,
            progress_color=COLORS['toggle_active'],
            border_width=0
        )
        self.merge_progress.pack(fill="x", padx=5, pady=5)
        self.merge_progress.set(0)

        # Status
        self.merge_status = ctk.CTkLabel(
            left_panel,
            text="Ready",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLORS['text']
        )
        self.merge_status.pack(pady=3)

        # Merge button
        ctk.CTkButton(
            left_panel,
            text="MERGE FILES",
            command=self.execute_merge,
            height=60,
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            fg_color=COLORS['button'],
            hover_color=COLORS['button_hover'],
            text_color="black",
            border_width=0
        ).pack(fill="x", padx=5, pady=5)

        # === RIGHT PANEL CONTENT ===
        ctk.CTkLabel(
            right_panel,
            text="File Preview",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=COLORS['text']
        ).grid(row=0, column=0, pady=10)

        self.merge_preview = ctk.CTkTextbox(
            right_panel,
            font=("Consolas", 10),
            wrap="none",
            border_width=0
        )
        self.merge_preview.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

    def setup_split_tab(self):
        """Setup Split File tab with responsive design"""
        # Left panel (controls) - takes 1/3 of space
        left_panel = ctk.CTkScrollableFrame(
            self.split_tab,
            fg_color="transparent",
            border_width=0
        )
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        # Right panel (preview) - takes 2/3 of space
        right_panel = ctk.CTkFrame(self.split_tab, fg_color="#0a0a0a", border_width=0)
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        right_panel.grid_rowconfigure(1, weight=1)
        right_panel.grid_columnconfigure(0, weight=1)

        # === LEFT PANEL CONTENT ===
        # Title
        title = ctk.CTkLabel(
            left_panel,
            text="Split File",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color=COLORS['text']
        )
        title.pack(pady=(5, 15))

        # Drag & Drop area
        drop_frame = ctk.CTkFrame(
            left_panel,
            fg_color=COLORS['bg_dark'],
            border_width=1,
            border_color="#3a3a3a",
            height=120
        )
        drop_frame.pack(fill="x", padx=5, pady=5)
        drop_frame.pack_propagate(False)

        self.split_placeholder = ctk.CTkLabel(
            drop_frame,
            text="📄 Drag & Drop a file here",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color="gray"
        )
        self.split_placeholder.pack(expand=True)

        # Enable drag and drop
        drop_frame.drop_target_register(DND_FILES)
        drop_frame.dnd_bind('<<Drop>>', self.on_split_drop)

        # Selected file info
        self.split_file_label = ctk.CTkLabel(
            left_panel,
            text="No file selected",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLORS['text'],
            wraplength=350
        )
        self.split_file_label.pack(pady=5)

        # Select button
        ctk.CTkButton(
            left_panel,
            text="Select File",
            command=self.select_split_file,
            height=50,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color=COLORS['button'],
            hover_color=COLORS['button_hover'],
            text_color="black",
            border_width=0
        ).pack(fill="x", padx=5, pady=5)

        # Settings
        settings_frame = ctk.CTkFrame(left_panel, fg_color="transparent", border_width=0)
        settings_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(
            settings_frame,
            text="Split Settings:",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=COLORS['text']
        ).pack(anchor="w", pady=3)

        # Rows per file
        rows_frame = ctk.CTkFrame(settings_frame, fg_color="transparent", border_width=0)
        rows_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(
            rows_frame,
            text="Rows per file:",
            text_color=COLORS['text'],
            width=100,
            font=ctk.CTkFont(family="Segoe UI", size=11)
        ).pack(side="left", padx=2)
        self.split_rows_entry = ctk.CTkEntry(
            rows_frame,
            height=35,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            border_width=0
        )
        self.split_rows_entry.insert(0, "1000")
        self.split_rows_entry.bind('<KeyRelease>', lambda e: self.update_split_calculation())
        self.split_rows_entry.pack(side="left", fill="x", expand=True, padx=2)

        # Calculation
        self.split_calc_label = ctk.CTkLabel(
            settings_frame,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color="gray"
        )
        self.split_calc_label.pack(anchor="w", pady=3)

        # Options
        options_frame = ctk.CTkFrame(left_panel, fg_color="transparent", border_width=0)
        options_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(
            options_frame,
            text="Options:",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=COLORS['text']
        ).pack(anchor="w", pady=3)

        self.split_keep_header = ctk.CTkSwitch(
            options_frame,
            text="Keep Headers",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLORS['text'],
            progress_color=COLORS['toggle_active'],
            button_color="gray",
            button_hover_color=COLORS['toggle_active']
        )
        self.split_keep_header.pack(anchor="w", pady=2)
        self.split_keep_header.select()

        self.split_skip_empty = ctk.CTkSwitch(
            options_frame,
            text="Skip Empty Rows",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLORS['text'],
            progress_color=COLORS['toggle_active'],
            button_color="gray",
            button_hover_color=COLORS['toggle_active']
        )
        self.split_skip_empty.pack(anchor="w", pady=2)
        self.split_skip_empty.select()

        self.split_remove_duplicates = ctk.CTkSwitch(
            options_frame,
            text="Remove Duplicates",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLORS['text'],
            progress_color=COLORS['toggle_active'],
            button_color="gray",
            button_hover_color=COLORS['toggle_active']
        )
        self.split_remove_duplicates.pack(anchor="w", pady=2)

        # Encoding & Delimiter & Format
        config_frame = ctk.CTkFrame(left_panel, fg_color="transparent", border_width=0)
        config_frame.pack(fill="x", padx=5, pady=5)

        enc_frame = ctk.CTkFrame(config_frame, fg_color="transparent", border_width=0)
        enc_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(
            enc_frame,
            text="Encoding:",
            text_color=COLORS['text'],
            width=80,
            font=ctk.CTkFont(family="Segoe UI", size=11)
        ).pack(side="left", padx=2)
        self.split_encoding = ctk.CTkComboBox(
            enc_frame,
            values=ENCODING_OPTIONS,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            button_color="#3a3a3a",  # Starts muted (Merge tab is active initially)
            button_hover_color="#4a4a4a",
            border_width=0,
            dropdown_hover_color="#3a3a3a",
            text_color=COLORS['text'],  # White text (inactive tab)
            dropdown_text_color=COLORS['text']
        )
        self.split_encoding.set('utf-8')
        self.split_encoding.pack(side="left", fill="x", expand=True, padx=2)

        delim_frame = ctk.CTkFrame(config_frame, fg_color="transparent", border_width=0)
        delim_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(
            delim_frame,
            text="Delimiter:",
            text_color=COLORS['text'],
            width=80,
            font=ctk.CTkFont(family="Segoe UI", size=11)
        ).pack(side="left", padx=2)
        self.split_delimiter = ctk.CTkComboBox(
            delim_frame,
            values=list(CSV_DELIMITERS.keys()),
            font=ctk.CTkFont(family="Segoe UI", size=11),
            button_color="#3a3a3a",  # Starts muted (Merge tab is active initially)
            button_hover_color="#4a4a4a",
            border_width=0,
            dropdown_hover_color="#3a3a3a",
            text_color=COLORS['text'],  # White text (inactive tab)
            dropdown_text_color=COLORS['text']
        )
        self.split_delimiter.set('Comma (,)')
        self.split_delimiter.pack(side="left", fill="x", expand=True, padx=2)

        format_frame = ctk.CTkFrame(config_frame, fg_color="transparent", border_width=0)
        format_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(
            format_frame,
            text="Format:",
            text_color=COLORS['text'],
            width=80,
            font=ctk.CTkFont(family="Segoe UI", size=11)
        ).pack(side="left", padx=2)
        self.split_output_format = ctk.CTkComboBox(
            format_frame,
            values=['Same as input', 'CSV', 'Excel (.xlsx)'],
            font=ctk.CTkFont(family="Segoe UI", size=11),
            button_color="#3a3a3a",  # Starts muted (Merge tab is active initially)
            button_hover_color="#4a4a4a",
            border_width=0,
            dropdown_hover_color="#3a3a3a",
            text_color=COLORS['text'],  # White text (inactive tab)
            dropdown_text_color=COLORS['text']
        )
        self.split_output_format.set('Same as input')
        self.split_output_format.pack(side="left", fill="x", expand=True, padx=2)

        # Progress
        self.split_progress = ctk.CTkProgressBar(
            left_panel,
            progress_color=COLORS['toggle_active'],
            border_width=0
        )
        self.split_progress.pack(fill="x", padx=5, pady=5)
        self.split_progress.set(0)

        # Status
        self.split_status = ctk.CTkLabel(
            left_panel,
            text="Ready",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLORS['text']
        )
        self.split_status.pack(pady=3)

        # Split button
        ctk.CTkButton(
            left_panel,
            text="SPLIT FILE",
            command=self.execute_split,
            height=60,
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            fg_color=COLORS['button'],
            hover_color=COLORS['button_hover'],
            text_color="black",
            border_width=0
        ).pack(fill="x", padx=5, pady=5)

        # === RIGHT PANEL CONTENT ===
        ctk.CTkLabel(
            right_panel,
            text="File Preview",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=COLORS['text']
        ).grid(row=0, column=0, pady=10)

        self.split_preview = ctk.CTkTextbox(
            right_panel,
            font=("Consolas", 10),
            wrap="none",
            border_width=0
        )
        self.split_preview.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

    # Merge Tab Methods
    def on_merge_drop(self, event):
        """Handle drag and drop for merge files"""
        files = self.root.tk.splitlist(event.data)
        valid_files = [f for f in files if Path(f).is_file()]
        if valid_files:
            self.add_files_to_merge(valid_files)

    def add_files_to_merge(self, files: List[str]):
        """Add files to merge list"""
        result = self.merger.add_files(files)
        for file in files:
            self.merge_file_listbox.insert(tk.END, Path(file).name)
            self.recent_files_manager.save_recent_file(file)

        self.merge_status.configure(text=f"Added {result['valid_count']} file(s). Total: {result['total_files']}")
        self.update_merge_placeholder()
        if result['valid_count'] > 0:
            self.show_merge_preview()

    def add_merge_files(self):
        """Add files via file dialog"""
        files = filedialog.askopenfilenames(
            title="Select files to merge",
            filetypes=[
                ("All Supported", "*.csv *.xlsx *.xls"),
                ("CSV Files", "*.csv"),
                ("Excel Files", "*.xlsx *.xls"),
                ("All Files", "*.*")
            ]
        )
        if files:
            self.add_files_to_merge(list(files))

    def remove_merge_file(self):
        """Remove selected file"""
        selection = self.merge_file_listbox.curselection()
        if selection:
            index = selection[0]
            self.merge_file_listbox.delete(index)
            if index < len(self.merger.files):
                del self.merger.files[index]
            self.merge_status.configure(text=f"File removed. Total: {len(self.merger.files)}")
            self.update_merge_placeholder()

    def clear_merge_files(self):
        """Clear all files"""
        self.merge_file_listbox.delete(0, tk.END)
        self.merger.clear_files()
        self.merge_preview.delete("1.0", tk.END)
        self.merge_status.configure(text="All files cleared")
        self.merge_progress.set(0)
        self.update_merge_placeholder()

    def update_merge_placeholder(self):
        """Update placeholder visibility"""
        if self.merge_file_listbox.size() == 0:
            self.merge_placeholder.pack(pady=10)
        else:
            self.merge_placeholder.pack_forget()

    def show_merge_preview(self):
        """Show preview of first file"""
        if self.merger.files:
            try:
                delimiter = CSV_DELIMITERS[self.merge_delimiter.get()]
                encoding = self.merge_encoding.get()

                df = DataFrameHelper.read_file(
                    self.merger.files[0],
                    encoding=encoding,
                    delimiter=delimiter
                )

                preview = df.head(PREVIEW_ROWS).to_string()
                self.merge_preview.delete("1.0", tk.END)
                self.merge_preview.insert("1.0", f"Preview of: {Path(self.merger.files[0]).name}\n\n{preview}")
            except Exception as e:
                self.merge_preview.delete("1.0", tk.END)
                self.merge_preview.insert("1.0", f"Error loading preview: {str(e)}")

    def execute_merge(self):
        """Execute merge operation"""
        if not self.merger.files:
            messagebox.showwarning("No Files", "Please add files to merge first.")
            return

        # Generate default filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"merged_{timestamp}.csv"

        # Ask for output location
        output_file = filedialog.asksaveasfilename(
            title="Save merged file as",
            initialfile=default_filename,
            defaultextension=".csv",
            filetypes=[
                ("CSV Files", "*.csv"),
                ("Excel Files", "*.xlsx"),
                ("All Files", "*.*")
            ]
        )

        if not output_file:
            return

        # Run merge in thread
        def merge_thread():
            try:
                self.root.after(0, lambda: self.merge_status.configure(text="Merging files..."))

                delimiter = CSV_DELIMITERS[self.merge_delimiter.get()]
                encoding = self.merge_encoding.get()

                result = self.merger.merge_files(
                    keep_header=self.merge_keep_header.get(),
                    skip_empty_rows=self.merge_skip_empty.get(),
                    remove_duplicates=self.merge_remove_duplicates.get(),
                    encoding=encoding,
                    delimiter=delimiter,
                    progress_callback=self.update_merge_progress
                )

                if result['success']:
                    save_result = self.merger.save_merged_file(
                        output_file,
                        encoding=encoding,
                        delimiter=delimiter
                    )

                    if save_result['success']:
                        stats = result['stats']
                        message = f"Merge completed successfully!\n\n" \
                                  f"Files merged: {stats['files_merged']}\n" \
                                  f"Total rows: {stats['total_rows_after']}\n" \
                                  f"Total columns: {stats['total_columns']}\n" \
                                  f"Duplicates removed: {stats['duplicates_removed']}\n\n" \
                                  f"Saved to: {output_file}"

                        self.root.after(0, lambda: messagebox.showinfo("Success", message))
                        self.root.after(0, lambda: self.merge_status.configure(text="Merge completed!"))
                    else:
                        self.root.after(0, lambda: messagebox.showerror("Error", save_result['error']))
                else:
                    self.root.after(0, lambda: messagebox.showerror("Error", result['error']))

            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Merge failed: {str(e)}"))
            finally:
                self.root.after(0, lambda: self.merge_progress.set(0))

        threading.Thread(target=merge_thread, daemon=True).start()

    def update_merge_progress(self, progress: float, message: str):
        """Update merge progress"""
        self.root.after(0, lambda: self.merge_progress.set(progress / 100))
        self.root.after(0, lambda: self.merge_status.configure(text=message))

    # Split Tab Methods
    def on_split_drop(self, event):
        """Handle drag and drop for split file"""
        files = self.root.tk.splitlist(event.data)
        if files:
            file = files[0]
            if Path(file).is_file():
                self.load_split_file(file)

    def select_split_file(self):
        """Select file via file dialog"""
        file = filedialog.askopenfilename(
            title="Select file to split",
            filetypes=[
                ("All Supported", "*.csv *.xlsx *.xls"),
                ("CSV Files", "*.csv"),
                ("Excel Files", "*.xlsx *.xls"),
                ("All Files", "*.*")
            ]
        )
        if file:
            self.load_split_file(file)

    def load_split_file(self, file: str):
        """Load file for splitting"""
        delimiter = CSV_DELIMITERS[self.split_delimiter.get()]
        encoding = self.split_encoding.get()

        result = self.splitter.load_file(file, encoding, delimiter)

        if result['success']:
            info = result['file_info']
            self.split_file_label.configure(
                text=f"{info['name']}\n{info['rows']} rows, {info['columns']} columns, {info['size']}"
            )
            self.split_placeholder.configure(text=f"✓ {info['name']}")
            self.recent_files_manager.save_recent_file(file)
            self.show_split_preview()
            self.update_split_calculation()
        else:
            messagebox.showerror("Error", result['error'])

    def show_split_preview(self):
        """Show preview of file to split"""
        preview_df = self.splitter.get_preview(PREVIEW_ROWS)
        if preview_df is not None:
            preview = preview_df.to_string()
            self.split_preview.delete("1.0", tk.END)
            self.split_preview.insert("1.0", f"Preview:\n\n{preview}")

    def update_split_calculation(self):
        """Update split calculation"""
        try:
            rows_per_file = int(self.split_rows_entry.get())
            calc = self.splitter.calculate_split_info(rows_per_file)

            if calc['num_files'] > 0:
                self.split_calc_label.configure(
                    text=f"Will create {calc['num_files']} file(s)\n"
                         f"Last file will have {calc['last_file_rows']} rows"
                )
            else:
                self.split_calc_label.configure(text="")
        except ValueError:
            self.split_calc_label.configure(text="Please enter a valid number")

    def execute_split(self):
        """Execute split operation"""
        if self.splitter.df is None:
            messagebox.showwarning("No File", "Please select a file to split first.")
            return

        try:
            rows_per_file = int(self.split_rows_entry.get())
            if rows_per_file <= 0:
                messagebox.showerror("Invalid Input", "Rows per file must be greater than 0.")
                return
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number for rows per file.")
            return

        # Ask for output directory
        output_dir = filedialog.askdirectory(title="Select output directory")

        if not output_dir:
            return

        # Determine output format
        format_choice = self.split_output_format.get()
        if format_choice == 'CSV':
            output_format = '.csv'
        elif format_choice == 'Excel (.xlsx)':
            output_format = '.xlsx'
        else:
            output_format = None

        # Run split in thread
        def split_thread():
            try:
                self.root.after(0, lambda: self.split_status.configure(text="Splitting file..."))

                delimiter = CSV_DELIMITERS[self.split_delimiter.get()]
                encoding = self.split_encoding.get()

                # Generate base filename with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                base_filename = f"split_{timestamp}"

                result = self.splitter.split_file(
                    rows_per_file=rows_per_file,
                    output_dir=output_dir,
                    base_filename=base_filename,
                    keep_header=self.split_keep_header.get(),
                    skip_empty_rows=self.split_skip_empty.get(),
                    remove_duplicates=self.split_remove_duplicates.get(),
                    encoding=encoding,
                    delimiter=delimiter,
                    output_format=output_format,
                    progress_callback=self.update_split_progress
                )

                if result['success']:
                    stats = result['stats']
                    message = f"Split completed successfully!\n\n" \
                              f"Original rows: {stats['original_rows']}\n" \
                              f"Files created: {stats['files_created']}\n" \
                              f"Duplicates removed: {stats['duplicates_removed']}\n\n" \
                              f"Saved to: {stats['output_directory']}"

                    self.root.after(0, lambda: messagebox.showinfo("Success", message))
                    self.root.after(0, lambda: self.split_status.configure(text="Split completed!"))
                else:
                    self.root.after(0, lambda: messagebox.showerror("Error", result['error']))

            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Split failed: {str(e)}"))
            finally:
                self.root.after(0, lambda: self.split_progress.set(0))

        threading.Thread(target=split_thread, daemon=True).start()

    def update_split_progress(self, progress: float, message: str):
        """Update split progress"""
        self.root.after(0, lambda: self.split_progress.set(progress / 100))
        self.root.after(0, lambda: self.split_status.configure(text=message))

    def run(self):
        """Run the application"""
        logger.info(f"Starting {APP_NAME} v{APP_VERSION}")
        self.root.mainloop()


def run_gui():
    """Run the GUI application"""
    app = CSVExcelManagerGUI()
    app.run()


if __name__ == "__main__":
    run_gui()
