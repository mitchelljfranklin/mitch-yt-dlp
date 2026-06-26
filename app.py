import os
import threading
from tkinter import filedialog, messagebox

import customtkinter as ctk

from downloader import Downloader


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Mitch-yt-dlp")
        self.geometry("600x400")
        self.minsize(520, 370)
        self.resizable(True, True)

        self.downloader = Downloader()
        self._poll_id = None

        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.grid(row=0, column=0, padx=10, pady=(5, 10), sticky="nsew")
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(0, weight=0)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_rowconfigure(2, weight=0)
        main_frame.grid_rowconfigure(3, weight=0)

        self.tabview = ctk.CTkTabview(
            main_frame,
            fg_color="#ffffff",
            segmented_button_fg_color="#e8e8e8",
            segmented_button_selected_color="#008cff",
            segmented_button_selected_hover_color="#0077dd",
            segmented_button_unselected_color="#e8e8e8",
            segmented_button_unselected_hover_color="#dddddd",
            text_color="#ffffff",
            text_color_disabled="#999999",
        )
        self.tabview.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 0))
        self.tabview.add("Download")
        tab = self.tabview.tab("Download")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=0)
        tab.grid_rowconfigure(1, weight=0)
        tab.grid_rowconfigure(2, weight=0)
        tab.grid_rowconfigure(3, weight=1)

        output_row = ctk.CTkFrame(tab, fg_color="transparent")
        output_row.grid(row=0, column=0, sticky="ew", pady=(10, 6))
        output_row.grid_columnconfigure(0, weight=1)
        output_row.grid_columnconfigure(1, weight=0)

        self.output_entry = ctk.CTkEntry(
            output_row, placeholder_text="Choose Output Folder", height=32
        )
        self.output_entry.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        browse_btn = ctk.CTkButton(
            output_row,
            text="Browse",
            width=70,
            height=32,
            fg_color="#e9ecef",
            hover_color="#dee2e6",
            text_color="#495057",
            border_width=1,
            border_color="#ced4da",
            command=self._browse_folder,
        )
        browse_btn.grid(row=0, column=1, sticky="e")

        self.url_entry = ctk.CTkEntry(
            tab, placeholder_text="Playlist or URL", height=36
        )
        self.url_entry.grid(row=1, column=0, sticky="ew", pady=6)

        toggle_row = ctk.CTkFrame(tab, fg_color="transparent")
        toggle_row.grid(row=2, column=0, sticky="ew", pady=(6, 10))
        toggle_row.grid_columnconfigure(0, weight=1)

        self.mp3_switch = ctk.CTkSwitch(
            toggle_row,
            text="Convert to MP3",
            progress_color="#008cff",
        )
        self.mp3_switch.grid(row=0, column=0, sticky="e", padx=(0, 10))

        bottom_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        bottom_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        bottom_frame.grid_columnconfigure(0, weight=0)
        bottom_frame.grid_columnconfigure(1, weight=0)
        bottom_frame.grid_columnconfigure(2, weight=1)
        bottom_frame.grid_columnconfigure(3, weight=0)

        self.stop_btn = ctk.CTkButton(
            bottom_frame,
            text="Stop",
            width=80,
            height=36,
            fg_color="#DB2843",
            hover_color="#c02038",
            command=self._stop,
        )
        self.stop_btn.grid(row=0, column=0, padx=(0, 6))

        self.cancel_btn = ctk.CTkButton(
            bottom_frame,
            text="Cancel",
            width=90,
            height=36,
            fg_color="#6C767D",
            hover_color="#5a6369",
            command=self._cancel,
        )
        self.cancel_btn.grid(row=0, column=1)

        self.start_btn = ctk.CTkButton(
            bottom_frame,
            text="Start",
            width=80,
            height=36,
            fg_color="#0085FC",
            hover_color="#0073dd",
            command=self._start,
        )
        self.start_btn.grid(row=0, column=3, sticky="e")

        self._set_buttons_state(idle=True)

        progress_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        progress_frame.grid(row=3, column=0, sticky="ew")
        progress_frame.grid_columnconfigure(0, weight=1)

        self.progress_bar = ctk.CTkProgressBar(progress_frame, height=10)
        self.progress_bar.grid(row=0, column=0, sticky="ew")
        self.progress_bar.set(0)

        self.progress_label = ctk.CTkLabel(
            progress_frame, text="", font=ctk.CTkFont(size=11), text_color="#666666"
        )
        self.progress_label.grid(row=1, column=0, sticky="ew", pady=(4, 2))

    def _browse_folder(self):
        folder = filedialog.askdirectory(title="Choose Output Folder")
        if folder:
            self.output_entry.delete(0, "end")
            self.output_entry.insert(0, folder)

    def _start(self):
        url = self.url_entry.get().strip()
        output = self.output_entry.get().strip()

        if not url:
            messagebox.showwarning("Missing URL", "Please enter a playlist or URL.")
            return
        if not output:
            messagebox.showwarning(
                "Missing Folder", "Please choose an output folder."
            )
            return

        to_mp3 = bool(self.mp3_switch.get())

        self._set_buttons_state(idle=False)
        self.progress_bar.set(0)
        self.progress_label.configure(text="Starting download...")

        self.downloader.download(url, output, to_mp3)
        self._poll_progress()

    def _stop(self):
        self.downloader.cancel()
        self._set_buttons_state(idle=True)
        self.progress_label.configure(text="Stopped.")

    def _cancel(self):
        self.downloader.cancel()
        self._set_buttons_state(idle=True)
        self.progress_bar.set(0)
        self.progress_label.configure(text="")
        self.url_entry.delete(0, "end")

    def _poll_progress(self):
        try:
            while True:
                data = self.downloader.progress_queue.get_nowait()
                status = data.get("status")

                if status == "downloading":
                    pct = data.get("percent", 0)
                    self.progress_bar.set(pct / 100)

                    speed = data.get("speed")
                    speed_str = ""
                    if speed:
                        if speed >= 1_000_000:
                            speed_str = f" {speed / 1_000_000:.1f} MB/s"
                        elif speed >= 1_000:
                            speed_str = f" {speed / 1_000:.0f} KB/s"
                        else:
                            speed_str = f" {speed:.0f} B/s"

                    eta = data.get("eta")
                    eta_str = ""
                    if eta and eta > 0:
                        m, s = divmod(eta, 60)
                        eta_str = f" - ETA {m}:{s:02d}"

                    self.progress_label.configure(
                        text=f"Downloading: {pct:.1f}%{speed_str}{eta_str}"
                    )

                elif status == "processing":
                    self.progress_bar.set(1)
                    self.progress_label.configure(text="Processing...")

                elif status == "completed":
                    self.progress_bar.set(1)
                    self.progress_label.configure(text="Download complete!")
                    self._set_buttons_state(idle=True)
                    return

                elif status == "cancelled":
                    self.progress_bar.set(0)
                    self.progress_label.configure(text="Cancelled.")
                    self._set_buttons_state(idle=True)
                    return

                elif status == "error":
                    self.progress_bar.set(0)
                    self.progress_label.configure(text="Error occurred.")
                    self._set_buttons_state(idle=True)
                    self.after(
                        50,
                        lambda: messagebox.showerror(
                            "Download Error", data.get("error", "Unknown error")
                        ),
                    )
                    return

        except queue.Empty:
            pass

        self._poll_id = self.after(120, self._poll_progress)

    def _set_buttons_state(self, idle):
        if idle:
            self.start_btn.configure(state="normal")
            self.stop_btn.configure(state="disabled")
            self.cancel_btn.configure(state="disabled")
        else:
            self.start_btn.configure(state="disabled")
            self.stop_btn.configure(state="normal")
            self.cancel_btn.configure(state="normal")

    def destroy(self):
        if self._poll_id:
            self.after_cancel(self._poll_id)
        self.downloader.cancel()
        super().destroy()
