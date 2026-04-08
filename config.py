"""
VocalFlow Configuration
-----------------------
Hardcoded API keys for testing/demo purposes.
In production, keys are stored in Windows Credential Manager via KeychainService.
If a key is set here, it will be used as the default on first launch.
"""

# Deepgram API key — used for speech-to-text
# Get yours free at: https://console.deepgram.com/signup
DEEPGRAM_API_KEY = "fcea8f017045391ccb0af1b50169c7dbce1323ea"

# Groq API key — optional, used for spelling/grammar/translation
# Get yours free at: https://console.groq.com
GROQ_API_KEY = ""

# Default model and language
DEFAULT_DEEPGRAM_MODEL    = "nova-3-general"
DEFAULT_DEEPGRAM_LANGUAGE = "multi"
DEFAULT_GROQ_MODEL        = "llama-3.3-70b-versatile"
DEFAULT_HOTKEY            = "right_alt"
DEFAULT_OVERLAY_THEME     = "Vibrant Blue"
