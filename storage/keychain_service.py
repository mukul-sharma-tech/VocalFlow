import json, os
import keyring

APP = "VocalFlow"
SETTINGS_FILE = os.path.join(os.path.expanduser("~"), ".vocalflow_settings.json")

class KeychainService:
    # API keys → Windows Credential Manager (encrypted)
    def store(self, k, v): keyring.set_password(APP, k, v)
    def retrieve(self, k): return keyring.get_password(APP, k) or ""
    def delete(self, k):
        try: keyring.delete_password(APP, k)
        except Exception: pass

class SettingsService:
    # Non-sensitive settings → JSON file in home directory
    def __init__(self):
        self._d = {}
        try:
            with open(SETTINGS_FILE) as f: self._d = json.load(f)
        except Exception: pass

    def get(self, k, default=None): return self._d.get(k, default)
    def set(self, k, v):
        self._d[k] = v
        try:
            with open(SETTINGS_FILE, "w") as f: json.dump(self._d, f, indent=2)
        except Exception: pass
