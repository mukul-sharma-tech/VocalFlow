import keyring
import json
import os

APP_NAME = "VocalFlow"
SETTINGS_FILE = os.path.join(os.path.expanduser("~"), ".vocalflow_settings.json")


class KeychainService:
    """Stores API keys in Windows Credential Manager via keyring."""

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
    """Persists non-sensitive settings to a JSON file."""

    def __init__(self):
        self._data = {}
        self._load()

    def _load(self):
        try:
            with open(SETTINGS_FILE, "r") as f:
                self._data = json.load(f)
        except Exception:
            self._data = {}

    def _save(self):
        try:
            with open(SETTINGS_FILE, "w") as f:
                json.dump(self._data, f, indent=2)
        except Exception:
            pass

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def set(self, key: str, value):
        self._data[key] = value
        self._save()
