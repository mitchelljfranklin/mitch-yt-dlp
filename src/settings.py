"""
Application preferences persistence.

Settings live in ``%APPDATA%\\Mitch-yt-dlp\\settings.json`` so the chosen
output folder and MP3 toggle survive restarts.  Loading is deliberately
forgiving: a missing, unreadable, or malformed file falls back to defaults.
"""

import json
import os

APPLICATION_DIRECTORY_NAME = "Mitch-yt-dlp"
SETTINGS_FILE_NAME = "settings.json"

DEFAULT_SETTINGS = {
    "output_directory": "",
    "convert_to_mp3": False,
}


def settings_file_path():
    """Return the per-user settings file path."""
    application_data = os.environ.get("APPDATA")
    if not application_data:
        application_data = os.path.join(os.path.expanduser("~"), ".config")
    return os.path.join(
        application_data, APPLICATION_DIRECTORY_NAME, SETTINGS_FILE_NAME
    )


def load_settings(path=None):
    """
    Load settings from *path*, falling back to defaults on any problem.

    Only keys with the expected value type are accepted, so a corrupted
    or hand-edited file cannot put the UI into an invalid state.
    """
    settings = dict(DEFAULT_SETTINGS)

    try:
        with open(path or settings_file_path(), "r", encoding="utf-8") as settings_file:
            stored_settings = json.load(settings_file)
    except OSError, ValueError:
        return settings

    if not isinstance(stored_settings, dict):
        return settings

    for key, default_value in DEFAULT_SETTINGS.items():
        stored_value = stored_settings.get(key)
        if isinstance(stored_value, type(default_value)):
            settings[key] = stored_value

    return settings


def save_settings(settings, path=None):
    """
    Write *settings* to *path* atomically.

    Returns ``True`` on success.  Write failures (for example a read-only
    profile) are ignored so a download can still start.
    """
    destination_path = path or settings_file_path()
    temporary_path = f"{destination_path}.tmp"

    try:
        os.makedirs(os.path.dirname(destination_path), exist_ok=True)
        with open(temporary_path, "w", encoding="utf-8") as settings_file:
            json.dump(settings, settings_file, indent=2)
        os.replace(temporary_path, destination_path)
    except OSError:
        return False

    return True
