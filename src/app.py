"""
Main application window.

Builds the customtkinter UI, wires up button handlers, and polls the
downloader's progress queue on the main thread so the GUI stays
responsive while yt-dlp runs in the background.
"""

import queue
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
    _COLOR_TAB_SELECTED = "#008cff"

    def __init__(self):
        super().__init__()

        self.title("Mitch-yt-dlp")
        self.geometry("600x400")
        self.minsize(520, 370)
        self.resizable(True, True)

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
            row=0, column=0, padx=10, pady=(5, 10), sticky="nsew"
        )
        main_container.grid_columnconfigure(0, weight=1)
        # Rows: 0 = tab bar, 1 = unused spacer, 2 = action buttons, 3 = progress
        main_container.grid_rowconfigure(0, weight=0)
        main_container.grid_rowconfigure(1, weight=1)
        main_container.grid_rowconfigure(2, weight=0)
        main_container.grid_rowconfigure(3, weight=0)

        self._build_tab_area(main_container)
        self._build_action_buttons(main_container)
        self._build_progress_area(main_container)

        # Buttons start in idle state (Start enabled, Stop/Cancel disabled)
        self._set_buttons_for_state(is_idle=True)

    def _build_tab_area(self, parent):
        """Create the tab view with Download tab and its form fields."""
        # Tab bar
        self.tab_view = ctk.CTkTabview(
            parent,
            fg_color="#ffffff",
            segmented_button_fg_color="#e8e8e8",
            segmented_button_selected_color=self._COLOR_TAB_SELECTED,
            segmented_button_selected_hover_color="#0077dd",
            segmented_button_unselected_color="#e8e8e8",
            segmented_button_unselected_hover_color="#dddddd",
            text_color="#ffffff",
            text_color_disabled="#999999",
        )
        self.tab_view.grid(
            row=0, column=0, columnspan=2, sticky="ew", pady=(0, 0)
        )
        self.tab_view.add("Download")
        download_tab = self.tab_view.tab("Download")
        download_tab.grid_columnconfigure(0, weight=1)
        download_tab.grid_rowconfigure(0, weight=0)  # output folder row
        download_tab.grid_rowconfigure(1, weight=0)  # URL row
        download_tab.grid_rowconfigure(2, weight=0)  # MP3 toggle row
        download_tab.grid_rowconfigure(3, weight=1)  # spacer

        self._build_output_folder_row(download_tab)
        self._build_url_input(download_tab)
        self._build_mp3_toggle(download_tab)

    def _build_output_folder_row(self, parent):
        """Output folder text field + Browse button on one row."""
        folder_row = ctk.CTkFrame(parent, fg_color="transparent")
        folder_row.grid(row=0, column=0, sticky="ew", pady=(10, 6))
        folder_row.grid_columnconfigure(0, weight=1)  # entry expands
        folder_row.grid_columnconfigure(1, weight=0)  # button fixed

        self.output_folder_entry = ctk.CTkEntry(
            folder_row, placeholder_text="Choose Output Folder", height=32
        )
        self.output_folder_entry.grid(
            row=0, column=0, sticky="ew", padx=(0, 6)
        )

        browse_button = ctk.CTkButton(
            folder_row,
            text="Browse",
            width=70,
            height=32,
            fg_color="#e9ecef",
            hover_color="#dee2e6",
            text_color="#495057",
            border_width=1,
            border_color="#ced4da",
            command=self._on_browse_folder,
        )
        browse_button.grid(row=0, column=1, sticky="e")

    def _build_url_input(self, parent):
        """URL / playlist text field."""
        self.url_entry = ctk.CTkEntry(
            parent, placeholder_text="Playlist or URL", height=36
        )
        self.url_entry.grid(row=1, column=0, sticky="ew", pady=6)

    def _build_mp3_toggle(self, parent):
        """"Convert to MP3" toggle switch, right-aligned."""
        mp3_row = ctk.CTkFrame(parent, fg_color="transparent")
        mp3_row.grid(row=2, column=0, sticky="ew", pady=(6, 10))
        mp3_row.grid_columnconfigure(0, weight=1)

        self.mp3_switch = ctk.CTkSwitch(
            mp3_row,
            text="Convert to MP3",
            progress_color=self._COLOR_TAB_SELECTED,
        )
        self.mp3_switch.grid(row=0, column=0, sticky="e", padx=(0, 10))

    def _build_action_buttons(self, parent):
        """Stop, Cancel, and Start button row."""
        buttons_frame = ctk.CTkFrame(parent, fg_color="transparent")
        buttons_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        buttons_frame.grid_columnconfigure(0, weight=0)  # Stop
        buttons_frame.grid_columnconfigure(1, weight=0)  # Cancel
        buttons_frame.grid_columnconfigure(2, weight=1)  # spacer
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

        self.cancel_button = ctk.CTkButton(
            buttons_frame,
            text="Cancel",
            width=90,
            height=36,
            fg_color=self._COLOR_CANCEL_GRAY,
            hover_color=self._COLOR_CANCEL_HOVER,
            command=self._on_cancel,
        )
        self.cancel_button.grid(row=0, column=1)

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
        progress_container.grid(row=3, column=0, sticky="ew")
        progress_container.grid_columnconfigure(0, weight=1)

        self.progress_bar = ctk.CTkProgressBar(progress_container, height=10)
        self.progress_bar.grid(row=0, column=0, sticky="ew")
        self.progress_bar.set(0)

        self.progress_label = ctk.CTkLabel(
            progress_container,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="#666666",
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
            messagebox.showwarning(
                "Missing URL", "Please enter a playlist or URL."
            )
            return
        if not output_directory:
            messagebox.showwarning(
                "Missing Folder", "Please choose an output folder."
            )
            return

        should_convert_to_mp3 = bool(self.mp3_switch.get())

        self._set_buttons_for_state(is_idle=False)
        self.progress_bar.set(0)
        self.progress_label.configure(text="Starting download...")

        # yt-dlp runs on its own thread; we poll the queue for progress
        self.downloader.download(video_url, output_directory, should_convert_to_mp3)
        self._poll_progress_queue()

    def _on_stop(self):
        """Cancel the download (leaves progress visible)."""
        self.downloader.cancel()
        self._set_buttons_for_state(is_idle=True)
        self.progress_label.configure(text="Stopped.")

    def _on_cancel(self):
        """Cancel the download and reset the form."""
        self.downloader.cancel()
        self._set_buttons_for_state(is_idle=True)
        self.progress_bar.set(0)
        self.progress_label.configure(text="")
        self.url_entry.delete(0, "end")

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
        elif current_status == Downloader.STATUS_PROCESSING:
            self.progress_bar.set(1)
            self.progress_label.configure(text="Processing...")
        elif current_status == Downloader.STATUS_COMPLETED:
            self.progress_bar.set(1)
            self.progress_label.configure(text="Download complete!")
            self._set_buttons_for_state(is_idle=True)
            self._cancel_polling()
        elif current_status == Downloader.STATUS_CANCELLED:
            self.progress_bar.set(0)
            self.progress_label.configure(text="Cancelled.")
            self._set_buttons_for_state(is_idle=True)
            self._cancel_polling()
        elif current_status == Downloader.STATUS_ERROR:
            self.progress_bar.set(0)
            self.progress_label.configure(text="Error occurred.")
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

        label_parts = [f"Downloading: {percent_done:.1f}%"]
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
            is_idle: If ``True``, Start is enabled and Stop/Cancel are
                     disabled (app is waiting for user input).  If
                     ``False``, the opposite.
        """
        if is_idle:
            self.start_button.configure(state="normal")
            self.stop_button.configure(state="disabled")
            self.cancel_button.configure(state="disabled")
        else:
            self.start_button.configure(state="disabled")
            self.stop_button.configure(state="normal")
            self.cancel_button.configure(state="normal")

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
