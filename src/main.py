"""
Mitch-yt-dlp — A modern Windows GUI for yt-dlp.

Entry point. Sets the appearance theme and launches the main application window.
"""

import os
import sys

# Allow importing sibling modules when running directly from src/
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import customtkinter as ctk

from app import App


def main():
    """Configure customtkinter and run the application event loop."""
    ctk.set_appearance_mode("system")
    ctk.set_default_color_theme("blue")

    application = App()
    application.mainloop()


if __name__ == "__main__":
    main()
