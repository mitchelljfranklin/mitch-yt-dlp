"""
Main application window.

Builds the customtkinter UI, wires up button handlers, and polls the
downloader's progress queue on the main thread so the GUI stays
responsive while yt-dlp runs in the background.
"""

import os
import queue
import sys
from tkinter import filedialog, messagebox

import customtkinter as ctk

from downloader import Downloader


class App(ctk.CTk):
    """The main Mitch-yt-dlp window."""

    # Polling interval (milliseconds) for reading the download progress queue
    _PROGRESS_POLL_INTERVAL_MS = 120

    # Color constants matching the mockup
    _COLOR_STOP_RED = "#DB2843"
    _COLOR_STOP_HOVER = "#c02038"
    _COLOR_CANCEL_GRAY = "#6C767D"
    _COLOR_CANCEL_HOVER = "#5a6369"
    _COLOR_START_BLUE = "#0085FC"
    _COLOR_START_HOVER = "#0073dd"
    _COLOR_ACCENT_BLUE = "#008cff"
    _COLOR_SUCCESS_GREEN = "#28a745"
    _LABEL_TEXT_COLOR = ("gray10", "gray90")

    def __init__(self):
        super().__init__()

        self.title("Mitch-yt-dlp")
        self.geometry("640x440")
        self.minsize(520, 370)
        self.resizable(True, True)

        icon_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "icon.ico",
        )
        if not os.path.exists(icon_path) and getattr(sys, "_MEIPASS", False):
            icon_path = os.path.join(sys._MEIPASS, "icon.ico")
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)

        self.downloader = Downloader()
        self._poll_callback_id = None  # ID returned by after() for progress polling

        self._build_user_interface()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_user_interface(self):
        """Build the full window layout: tabs, inputs, buttons, progress bar."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.grid(
            row=0, column=0, padx=14, pady=(10, 10), sticky="nsew"
        )
        main_container.grid_columnconfigure(0, weight=1)
        # Rows: 0=form, 1=validation, 2=separator, 3=buttons,
        #       4=playlist, 5=progress, 6=bottom spacer
        main_container.grid_rowconfigure(0, weight=0)
        main_container.grid_rowconfigure(1, weight=0)
        main_container.grid_rowconfigure(2, weight=0)
        main_container.grid_rowconfigure(3, weight=0)
        main_container.grid_rowconfigure(4, weight=0)
        main_container.grid_rowconfigure(5, weight=0)
        main_container.grid_rowconfigure(6, weight=1)

        self._build_form_area(main_container)

        # Inline validation label
        self.validation_label = ctk.CTkLabel(
            main_container,
            text="",
            text_color=self._COLOR_STOP_RED,
            font=ctk.CTkFont(size=11),
        )
        self.validation_label.grid(row=1, column=0, sticky="w", pady=(2, 0))

        # Separator line
        separator = ctk.CTkFrame(
            main_container, height=1, fg_color=("gray70", "gray35")
        )
        separator.grid(row=2, column=0, sticky="ew", pady=(6, 6))

        self._build_action_buttons(main_container)

        # Playlist progress (below buttons, above progress bar)
        self.playlist_label = ctk.CTkLabel(
            main_container,
            text="",
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.playlist_label.grid(
            row=4, column=0, sticky="w", pady=(4, 2)
        )

        self._build_progress_area(main_container)

        # Bottom spacer (absorbs extra window height)
        ctk.CTkFrame(main_container, height=0, fg_color="transparent").grid(
            row=6, column=0, sticky="ew"
        )

        # Buttons start in idle state (Start enabled, Stop disabled)
        self._set_buttons_for_state(is_idle=True)

        # Keyboard shortcuts
        self.bind("<Return>", lambda _e: self._on_start())
        self.bind("<Escape>", lambda _e: self._on_escape())

    def _build_form_area(self, parent):
        """Build the form content: header, labels, inputs, toggle."""
        form_frame = ctk.CTkFrame(parent, fg_color="transparent")
        form_frame.grid(row=0, column=0, columnspan=2, sticky="ew")
        form_frame.grid_columnconfigure(0, weight=1)

        # Header
        header = ctk.CTkLabel(
            form_frame,
            text="Mitch YT-DLP Downloader",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        header.grid(row=0, column=0, sticky="w", pady=(0, 6))

        # Output folder label
        folder_label = ctk.CTkLabel(
            form_frame,
            text="Output Folder",
            font=ctk.CTkFont(size=12),
        )
        folder_label.grid(row=2, column=0, sticky="w", pady=(2, 1))

        # Output folder row (entry + Browse)
        self._build_output_folder_row(form_frame, row=3)

        # Video URL label
        url_label = ctk.CTkLabel(
            form_frame,
            text="Video URL",
            font=ctk.CTkFont(size=12),
        )
        url_label.grid(row=4, column=0, sticky="w", pady=(6, 1))

        # URL entry
        self._build_url_input(form_frame, row=5)

        # MP3 toggle + hint
        self._build_mp3_toggle(form_frame, row=6)

    def _build_output_folder_row(self, parent, row):
        """Output folder text field + Browse button on one row."""
        folder_row = ctk.CTkFrame(parent, fg_color="transparent")
        folder_row.grid(row=row, column=0, sticky="ew", pady=(0, 4))
        folder_row.grid_columnconfigure(0, weight=1)  # entry expands
        folder_row.grid_columnconfigure(1, weight=0)  # button fixed

        self.output_folder_entry = ctk.CTkEntry(
            folder_row, placeholder_text="e.g. C:\\Users\\...\\Videos", height=36
        )
        self.output_folder_entry.grid(
            row=0, column=0, sticky="ew", padx=(0, 6)
        )

        browse_button = ctk.CTkButton(
            folder_row,
            text="Browse",
            width=70,
            height=36,
            fg_color="transparent",
            border_width=1,
            command=self._on_browse_folder,
        )
        browse_button.grid(row=0, column=1, sticky="e")

    def _build_url_input(self, parent, row):
        """URL / playlist text field."""
        self.url_entry = ctk.CTkEntry(
            parent, placeholder_text="URL or Playlist", height=36
        )
        self.url_entry.grid(row=row, column=0, sticky="ew", pady=(0, 4))

    def _build_mp3_toggle(self, parent, row):
        """"Convert to MP3" toggle switch + hint, right-aligned."""
        mp3_row = ctk.CTkFrame(parent, fg_color="transparent")
        mp3_row.grid(row=row, column=0, sticky="ew", pady=(6, 0))
        mp3_row.grid_columnconfigure(0, weight=1)

        toggle_container = ctk.CTkFrame(mp3_row, fg_color="transparent")
        toggle_container.grid(row=0, column=0, sticky="e", padx=(0, 8))
        toggle_container.grid_columnconfigure(0, weight=1)

        self.mp3_switch = ctk.CTkSwitch(
            toggle_container,
            text="Convert to MP3",
            progress_color=self._COLOR_ACCENT_BLUE,
        )
        self.mp3_switch.grid(row=0, column=0, sticky="e")

        mp3_hint = ctk.CTkLabel(
            toggle_container,
            text="Extracts audio with FFmpeg",
            font=ctk.CTkFont(size=10),
        )
        mp3_hint.grid(row=1, column=0, sticky="e")

    def _build_action_buttons(self, parent):
        """Stop, Cancel, and Start button row."""
        buttons_frame = ctk.CTkFrame(parent, fg_color="transparent")
        buttons_frame.grid(row=3, column=0, sticky="ew", pady=(0, 6))
        buttons_frame.grid_columnconfigure(0, weight=0)  # Stop
        buttons_frame.grid_columnconfigure(1, weight=1)  # spacer
        buttons_frame.grid_columnconfigure(2, weight=0)  # Exit
        buttons_frame.grid_columnconfigure(3, weight=0)  # Start

        self.stop_button = ctk.CTkButton(
            buttons_frame,
            text="Stop",
            width=80,
            height=36,
            fg_color=self._COLOR_STOP_RED,
            hover_color=self._COLOR_STOP_HOVER,
            command=self._on_stop,
        )
        self.stop_button.grid(row=0, column=0, padx=(0, 6))

        self.exit_button = ctk.CTkButton(
            buttons_frame,
            text="Exit",
            width=80,
            height=36,
            fg_color=self._COLOR_CANCEL_GRAY,
            hover_color=self._COLOR_CANCEL_HOVER,
            command=self.destroy,
        )
        self.exit_button.grid(row=0, column=2, padx=(0, 6))

        self.start_button = ctk.CTkButton(
            buttons_frame,
            text="Start",
            width=80,
            height=36,
            fg_color=self._COLOR_START_BLUE,
            hover_color=self._COLOR_START_HOVER,
            command=self._on_start,
        )
        self.start_button.grid(row=0, column=3, sticky="e")

    def _build_progress_area(self, parent):
        """Progress bar and status label at the bottom of the window."""
        progress_container = ctk.CTkFrame(parent, fg_color="transparent")
        progress_container.grid(row=5, column=0, sticky="ew")
        progress_container.grid_columnconfigure(0, weight=1)

        self.progress_bar = ctk.CTkProgressBar(
            progress_container,
            height=12,
            progress_color=self._COLOR_START_BLUE,
        )
        self.progress_bar.grid(row=0, column=0, sticky="ew")
        self.progress_bar.set(0)

        self.progress_label = ctk.CTkLabel(
            progress_container,
            text="",
            font=ctk.CTkFont(size=11),
        )
        self.progress_label.grid(row=1, column=0, sticky="ew", pady=(4, 2))

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_browse_folder(self):
        """Open a folder-picker dialog and populate the output field."""
        selected_folder = filedialog.askdirectory(title="Choose Output Folder")
        if selected_folder:
            self.output_folder_entry.delete(0, "end")
            self.output_folder_entry.insert(0, selected_folder)

    def _on_start(self):
        """Validate inputs and launch the download."""
        video_url = self.url_entry.get().strip()
        output_directory = self.output_folder_entry.get().strip()

        if not video_url:
            self._show_validation_error("Please enter a URL or playlist.")
            self.url_entry.focus_set()
            return
        if not output_directory:
            self._show_validation_error("Please choose an output folder.")
            self.output_folder_entry.focus_set()
            return

        should_convert_to_mp3 = bool(self.mp3_switch.get())

        self._set_buttons_for_state(is_idle=False)
        self.progress_bar.set(0)
        self.playlist_label.configure(text="")
        self.progress_label.configure(
            text="Starting download...", text_color=self._LABEL_TEXT_COLOR
        )
        self._hide_validation()

        # yt-dlp runs on its own thread; we poll the queue for progress
        self.downloader.download(video_url, output_directory, should_convert_to_mp3)
        self._poll_progress_queue()

    def _on_stop(self):
        """Cancel the download (leaves progress visible)."""
        self.downloader.cancel()
        self._set_buttons_for_state(is_idle=True)
        self.progress_label.configure(text="Stopped.")

    def _on_escape(self):
        """Handle Escape key: stop download if active."""
        if self._poll_callback_id is not None:
            self._on_stop()

    def _show_validation_error(self, message):
        """Display an inline validation error that auto-clears."""
        self.validation_label.configure(text=message)
        self.after(4000, self._hide_validation)

    def _hide_validation(self):
        """Clear the inline validation message."""
        self.validation_label.configure(text="")

    # ------------------------------------------------------------------
    # Progress polling (runs on the main thread via after())
    # ------------------------------------------------------------------

    def _poll_progress_queue(self):
        """
        Drain the downloader's progress queue and update the UI.

        Called every ``_PROGRESS_POLL_INTERVAL_MS`` ms via tkinter's
        ``after()``.  Because this runs on the main thread we can safely
        update widgets without locking.
        """
        try:
            while True:
                progress_data = self.downloader.progress_queue.get_nowait()
                self._handle_progress_update(progress_data)
        except queue.Empty:
            pass

        # Schedule the next poll
        self._poll_callback_id = self.after(
            self._PROGRESS_POLL_INTERVAL_MS, self._poll_progress_queue
        )

    def _handle_progress_update(self, data):
        """Dispatch a single progress message to the appropriate handler."""
        current_status = data.get("status")

        if current_status == Downloader.STATUS_DOWNLOADING:
            self._show_downloading_progress(data)
            playlist_index = data.get("playlist_index")
            playlist_count = data.get("playlist_count")
            if playlist_index is not None:
                if playlist_count and playlist_count > 1:
                    self.playlist_label.configure(
                        text=f"Video {playlist_index} / {playlist_count}"
                    )
                else:
                    self.playlist_label.configure(
                        text=f"Video {playlist_index}"
                    )
        elif current_status == Downloader.STATUS_PROCESSING:
            self.progress_bar.set(1)
            self.progress_label.configure(text="Processing...")
        elif current_status == Downloader.STATUS_COMPLETED:
            self.progress_bar.set(1)
            self.progress_label.configure(
                text="Download complete!",
                text_color=self._COLOR_SUCCESS_GREEN,
            )
            self.playlist_label.configure(text="")
            self._set_buttons_for_state(is_idle=True)
            self._cancel_polling()
        elif current_status == Downloader.STATUS_CANCELLED:
            self.progress_bar.set(0)
            self.progress_label.configure(text="Cancelled.")
            self.playlist_label.configure(text="")
            self._set_buttons_for_state(is_idle=True)
            self._cancel_polling()
        elif current_status == Downloader.STATUS_ERROR:
            self.progress_bar.set(0)
            self.progress_label.configure(text="Error occurred.")
            self.playlist_label.configure(text="")
            self._set_buttons_for_state(is_idle=True)
            self._cancel_polling()
            error_message = data.get("error", "Unknown error")
            self.after(
                50,
                lambda msg=error_message: messagebox.showerror(
                    "Download Error", msg
                ),
            )

    def _show_downloading_progress(self, data):
        """Update the progress bar and label with download stats."""
        percent_done = data.get("percent", 0)
        self.progress_bar.set(percent_done / 100)

        speed_text = self._format_speed(data.get("speed"))
        eta_text = self._format_eta(data.get("eta"))

        label_parts = [f"\u2b07\ufe0f Downloading: {percent_done:.1f}%"]
        if speed_text:
            label_parts.append(speed_text)
        if eta_text:
            label_parts.append(eta_text)

        self.progress_label.configure(text=" ".join(label_parts))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _format_speed(bytes_per_second):
        """Return a human-readable speed string, or ``""`` if ``None``."""
        if not bytes_per_second:
            return ""
        if bytes_per_second >= 1_000_000:
            return f"{bytes_per_second / 1_000_000:.1f} MB/s"
        if bytes_per_second >= 1_000:
            return f"{bytes_per_second / 1_000:.0f} KB/s"
        return f"{bytes_per_second:.0f} B/s"

    @staticmethod
    def _format_eta(seconds_remaining):
        """Return an ETA string like ``"- ETA 2:35"`` or ``""`` if ``None``."""
        if not seconds_remaining or seconds_remaining <= 0:
            return ""
        minutes, seconds = divmod(int(seconds_remaining), 60)
        return f"- ETA {minutes}:{seconds:02d}"

    def _set_buttons_for_state(self, is_idle):
        """
        Enable / disable buttons based on application state.

        Args:
            is_idle: If ``True``, Start is enabled and Stop is
                     disabled (app is waiting for user input).  If
                     ``False``, the opposite.
        """
        if is_idle:
            self.start_button.configure(state="normal")
            self.stop_button.configure(state="disabled")
        else:
            self.start_button.configure(state="disabled")
            self.stop_button.configure(state="normal")

    def _cancel_polling(self):
        """Stop the periodic progress-queue polling loop."""
        if self._poll_callback_id is not None:
            self.after_cancel(self._poll_callback_id)
            self._poll_callback_id = None

    # ------------------------------------------------------------------
    # Window lifecycle
    # ------------------------------------------------------------------

    def destroy(self):
        """Clean up before closing the window."""
        self._cancel_polling()
        self.downloader.cancel()
        super().destroy()
