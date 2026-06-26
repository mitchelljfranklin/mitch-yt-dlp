"""
Main application window.

Builds the ttkbootstrap UI, wires up button handlers, and polls the
downloader's progress queue on the main thread so the GUI stays
responsive while yt-dlp runs in the background.
"""

import os
import queue
import sys
from tkinter import filedialog, messagebox

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from downloader import Downloader


class App(ttk.Window):
    """The main Mitch-yt-dlp window."""

    _PROGRESS_POLL_INTERVAL_MS = 120

    def __init__(self):
        super().__init__(themename="superhero")

        self.title("Mitch-yt-dlp")
        self.geometry("640x366")
        self.minsize(520, 362)

        style = ttk.Style()
        style.configure("TProgressbar", thickness=16)
        self.resizable(False, False)

        icon_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "icon.ico",
        )
        if not os.path.exists(icon_path) and getattr(sys, "_MEIPASS", False):
            icon_path = os.path.join(sys._MEIPASS, "icon.ico")
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)

        self.downloader = Downloader()
        self._poll_callback_id = None

        self._build_user_interface()

    def _build_user_interface(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        main_container = ttk.Frame(self, padding=(14, 10, 14, 2))
        main_container.grid(row=0, column=0, sticky="nsew")
        main_container.grid_columnconfigure(0, weight=1)
        main_container.grid_rowconfigure(0, weight=0)
        main_container.grid_rowconfigure(1, weight=0)
        main_container.grid_rowconfigure(2, weight=0)
        main_container.grid_rowconfigure(3, weight=0)
        main_container.grid_rowconfigure(4, weight=0)
        main_container.grid_rowconfigure(5, weight=0)
        main_container.grid_rowconfigure(6, weight=1)

        self._build_form_area(main_container)

        # Inline validation label
        self.validation_label = ttk.Label(
            main_container,
            text="",
            bootstyle="danger",
            font=("", 10),
        )
        self.validation_label.grid(row=1, column=0, sticky="w", pady=(2, 0))

        # Separator
        separator = ttk.Separator(main_container, orient="horizontal")
        separator.grid(row=2, column=0, sticky="ew", pady=(6, 6))

        self._build_action_buttons(main_container)

        # Playlist progress
        self.playlist_label = ttk.Label(
            main_container,
            text="",
            font=("", 11, "bold"),
        )
        self.playlist_label.grid(row=4, column=0, sticky="w", pady=(4, 2))

        self._build_progress_area(main_container)

        # Bottom spacer
        ttk.Frame(main_container).grid(row=6, column=0, sticky="ew")

        self._set_buttons_for_state(is_idle=True)

        self.bind("<Return>", lambda _e: self._on_start())
        self.bind("<Escape>", lambda _e: self._on_escape())

    def _build_form_area(self, parent):
        form_frame = ttk.Frame(parent)
        form_frame.grid(row=0, column=0, columnspan=2, sticky="ew")
        form_frame.grid_columnconfigure(0, weight=1)

        # Header
        header = ttk.Label(
            form_frame,
            text="Mitch YT-DLP Downloader",
            font=("", 14, "bold"),
            bootstyle="primary",
        )
        header.grid(row=0, column=0, sticky="w", pady=(0, 6))

        # Output folder label
        folder_label = ttk.Label(
            form_frame,
            text="Output Folder",
            font=("", 11),
        )
        folder_label.grid(row=2, column=0, sticky="w", pady=(2, 1))

        self._build_output_folder_row(form_frame, row=3)

        # Video URL label
        url_label = ttk.Label(
            form_frame,
            text="Video URL",
            font=("", 11),
        )
        url_label.grid(row=4, column=0, sticky="w", pady=(6, 1))

        self._build_url_input(form_frame, row=5)

        self._build_mp3_toggle(form_frame, row=6)

    def _build_output_folder_row(self, parent, row):
        folder_row = ttk.Frame(parent)
        folder_row.grid(row=row, column=0, sticky="ew", pady=(0, 4))
        folder_row.grid_columnconfigure(0, weight=1)
        folder_row.grid_columnconfigure(1, weight=0)

        self.output_folder_entry = ttk.Entry(
            folder_row,
        )
        self.output_folder_entry.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        browse_button = ttk.Button(
            folder_row,
            text="Browse",
            bootstyle="outline-primary",
            command=self._on_browse_folder,
        )
        browse_button.grid(row=0, column=1, sticky="e")

    def _build_url_input(self, parent, row):
        self.url_entry = ttk.Entry(parent)
        self.url_entry.grid(row=row, column=0, sticky="ew", pady=(0, 4))

    def _build_mp3_toggle(self, parent, row):
        mp3_row = ttk.Frame(parent)
        mp3_row.grid(row=row, column=0, sticky="ew", pady=(6, 0))
        mp3_row.grid_columnconfigure(0, weight=1)

        toggle_container = ttk.Frame(mp3_row)
        toggle_container.grid(row=0, column=0, sticky="e", padx=(0, 8))
        toggle_container.grid_columnconfigure(0, weight=1)

        self.mp3_switch = ttk.Checkbutton(
            toggle_container,
            text="Convert to MP3",
            bootstyle="primary-round-toggle",
        )
        self.mp3_switch.grid(row=0, column=0, sticky="e")

        mp3_hint = ttk.Label(
            toggle_container,
            text="Extracts audio with FFmpeg",
            font=("", 9),
            bootstyle="secondary",
        )
        mp3_hint.grid(row=1, column=0, sticky="e")

    def _build_action_buttons(self, parent):
        buttons_frame = ttk.Frame(parent)
        buttons_frame.grid(row=3, column=0, sticky="ew", pady=(0, 6))
        buttons_frame.grid_columnconfigure(0, weight=0)
        buttons_frame.grid_columnconfigure(1, weight=1)
        buttons_frame.grid_columnconfigure(2, weight=0)
        buttons_frame.grid_columnconfigure(3, weight=0)

        self.stop_button = ttk.Button(
            buttons_frame,
            text="Stop",
            bootstyle="danger",
            command=self._on_stop,
        )
        self.stop_button.grid(row=0, column=0, padx=(0, 6))

        self.exit_button = ttk.Button(
            buttons_frame,
            text="Exit",
            bootstyle="secondary",
            command=self.destroy,
        )
        self.exit_button.grid(row=0, column=2, padx=(0, 6))

        self.start_button = ttk.Button(
            buttons_frame,
            text="Start",
            bootstyle="primary",
            command=self._on_start,
        )
        self.start_button.grid(row=0, column=3, sticky="e")

    def _build_progress_area(self, parent):
        progress_container = ttk.Frame(parent)
        progress_container.grid(row=5, column=0, sticky="ew")
        progress_container.grid_columnconfigure(0, weight=1)

        self.progress_bar = ttk.Progressbar(
            progress_container,
            bootstyle="primary-striped",
            maximum=100,
            value=0,
        )
        self.progress_bar.grid(row=0, column=0, sticky="ew")

        self.progress_label = ttk.Label(
            progress_container,
            text="",
            font=("", 10),
        )
        self.progress_label.grid(row=1, column=0, sticky="ew", pady=(4, 2))

    # ---- Event handlers --------------------------------------------------

    def _on_browse_folder(self):
        selected_folder = filedialog.askdirectory(title="Choose Output Folder")
        if selected_folder:
            self.output_folder_entry.delete(0, "end")
            self.output_folder_entry.insert(0, selected_folder)

    def _on_start(self):
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

        should_convert_to_mp3 = self.mp3_switch.instate(["selected"])

        self._set_buttons_for_state(is_idle=False)
        self.progress_bar["value"] = 0
        self.playlist_label.configure(text="")
        self.progress_label.configure(text="Starting download...")
        self._hide_validation()

        self.downloader.download(video_url, output_directory,
                                 should_convert_to_mp3)
        self._poll_progress_queue()

    def _on_stop(self):
        self.downloader.cancel()
        self._set_buttons_for_state(is_idle=True)
        self.progress_label.configure(text="Stopped.")

    def _on_escape(self):
        if self._poll_callback_id is not None:
            self._on_stop()

    def _show_validation_error(self, message):
        self.validation_label.configure(text=message)
        self.after(4000, self._hide_validation)

    def _hide_validation(self):
        self.validation_label.configure(text="")

    def _poll_progress_queue(self):
        try:
            while True:
                progress_data = self.downloader.progress_queue.get_nowait()
                self._handle_progress_update(progress_data)
        except queue.Empty:
            pass

        self._poll_callback_id = self.after(
            self._PROGRESS_POLL_INTERVAL_MS, self._poll_progress_queue
        )

    def _handle_progress_update(self, data):
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
            self.progress_bar["value"] = 100
            self.progress_label.configure(text="Processing...")
        elif current_status == Downloader.STATUS_COMPLETED:
            self.progress_bar["value"] = 100
            self.progress_label.configure(
                text="Download complete!",
                bootstyle="success",
            )
            self.playlist_label.configure(text="")
            self._set_buttons_for_state(is_idle=True)
            self._cancel_polling()
        elif current_status == Downloader.STATUS_CANCELLED:
            self.progress_bar["value"] = 0
            self.progress_label.configure(text="Cancelled.")
            self.playlist_label.configure(text="")
            self._set_buttons_for_state(is_idle=True)
            self._cancel_polling()
        elif current_status == Downloader.STATUS_ERROR:
            self.progress_bar["value"] = 0
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
        percent_done = data.get("percent", 0)
        self.progress_bar["value"] = int(percent_done)

        speed_text = self._format_speed(data.get("speed"))
        eta_text = self._format_eta(data.get("eta"))

        label_parts = [f"\u2b07\ufe0f Downloading: {percent_done:.1f}%"]
        if speed_text:
            label_parts.append(speed_text)
        if eta_text:
            label_parts.append(eta_text)

        self.progress_label.configure(text=" ".join(label_parts))

    def _set_buttons_for_state(self, is_idle):
        if is_idle:
            self.start_button.configure(state="normal")
            self.stop_button.configure(state="disabled")
        else:
            self.start_button.configure(state="disabled")
            self.stop_button.configure(state="normal")

    def _cancel_polling(self):
        if self._poll_callback_id is not None:
            self.after_cancel(self._poll_callback_id)
            self._poll_callback_id = None

    def destroy(self):
        self._cancel_polling()
        self.downloader.cancel()
        super().destroy()

    @staticmethod
    def _format_speed(bytes_per_second):
        if not bytes_per_second:
            return ""
        if bytes_per_second >= 1_000_000:
            return f"{bytes_per_second / 1_000_000:.1f} MB/s"
        if bytes_per_second >= 1_000:
            return f"{bytes_per_second / 1_000:.0f} KB/s"
        return f"{bytes_per_second:.0f} B/s"

    @staticmethod
    def _format_eta(seconds_remaining):
        if not seconds_remaining or seconds_remaining <= 0:
            return ""
        minutes, seconds = divmod(int(seconds_remaining), 60)
        return f"- ETA {minutes}:{seconds:02d}"
