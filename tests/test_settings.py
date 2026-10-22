import json
import os

import pytest

from settings import DEFAULT_SETTINGS, load_settings, save_settings


def test_missing_file_returns_defaults(tmp_path):
    assert load_settings(tmp_path / "absent.json") == DEFAULT_SETTINGS


def test_roundtrip(tmp_path):
    settings_path = tmp_path / "nested" / "settings.json"
    settings = {"output_directory": r"C:\Downloads", "convert_to_mp3": True}

    assert save_settings(settings, settings_path) is True
    assert load_settings(settings_path) == settings


def test_invalid_json_returns_defaults(tmp_path):
    settings_path = tmp_path / "settings.json"
    settings_path.write_text("{not json", encoding="utf-8")

    assert load_settings(settings_path) == DEFAULT_SETTINGS


@pytest.mark.parametrize("payload", ["[]", '"text"', "42", "null"])
def test_non_dict_payload_returns_defaults(tmp_path, payload):
    settings_path = tmp_path / "settings.json"
    settings_path.write_text(payload, encoding="utf-8")

    assert load_settings(settings_path) == DEFAULT_SETTINGS


def test_wrong_value_types_are_ignored(tmp_path):
    settings_path = tmp_path / "settings.json"
    settings_path.write_text(
        json.dumps({"output_directory": 5, "convert_to_mp3": "yes"}),
        encoding="utf-8",
    )

    assert load_settings(settings_path) == DEFAULT_SETTINGS


def test_unknown_keys_are_dropped(tmp_path):
    settings_path = tmp_path / "settings.json"
    settings_path.write_text(
        json.dumps(
            {
                "output_directory": r"D:\Media",
                "convert_to_mp3": True,
                "unexpected": "value",
            }
        ),
        encoding="utf-8",
    )

    loaded_settings = load_settings(settings_path)

    assert loaded_settings == {
        "output_directory": r"D:\Media",
        "convert_to_mp3": True,
    }


def test_save_leaves_no_temporary_file(tmp_path):
    settings_path = tmp_path / "settings.json"

    save_settings({"output_directory": "", "convert_to_mp3": False}, settings_path)

    assert sorted(entry.name for entry in tmp_path.iterdir()) == ["settings.json"]


def test_save_failure_is_reported(tmp_path):
    blocking_file = tmp_path / "blocking"
    blocking_file.write_text("not a directory", encoding="utf-8")

    settings_path = os.path.join(str(blocking_file), "settings.json")

    assert (
        save_settings({"output_directory": "", "convert_to_mp3": False}, settings_path)
        is False
    )
