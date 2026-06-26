"""
Mitch-yt-dlp — A modern themed Windows GUI for yt-dlp using ttkbootstrap.

Entry point. Configures the theme and launches the main application window.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import App


def main():
    application = App()
    application.mainloop()


if __name__ == "__main__":
    main()
