"""
Two storage layers:
  - KeychainService  → API keys go into Windows Credential Manager (encrypted, secure)
  - SettingsService  → Everything else goes into a JSON file in the user's home folder
"""
import json
import os

import keyring

APP_NAME      = "VocalFlow"
SETTINGS_FILE = os.path.join(os.path.expanduser("~"), ".vocalflow_settings.json")


class KeychainService:
    """Wraps Windows Credential Manager via the `keyring` library."""

    def store(self, key: str, value: str):
        keyring.set_password(APP_NAME, key, value)

    def retrieve(self, key: str) -> str:
        return keyring.get_password(APP_NAME, key) or ""

    def delete(self, key: str):
        try:
            keyring.delete_password(APP_NAME, key)
        except Exception:
            pass


class SettingsService:
    """Simple JSON-backed key-value store for non-sensitive preferences."""

    def __init__(self):
        self._data: dict = {}
        self._load()

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def set(self, key: str, value):
        self._data[key] = value
        self._save()

    def _load(self):
        try:
            with open(SETTINGS_FILE) as f:
                self._data = json.load(f)
        except Exception:
            self._data = {}  # first run or corrupted file — start fresh

    def _save(self):
        try:
            with open(SETTINGS_FILE, "w") as f:
                json.dump(self._data, f, indent=2)
        except Exception:
            pass
