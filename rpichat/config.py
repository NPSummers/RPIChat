"""Configuration loading and defaults."""
import json
import os

CONFIG_PATH = 'config.json'
DEFAULT_CONFIG = {
    'port': 2022,
    'host_key': 'ssh_host_key',
    'user_db': 'users.json',
    'login_banner': 'Welcome to RPIChat! Type "register" to register or login with your account.',
    'username_min_len': 3,
    'username_max_len': 20,
    'login_rate_limit': 5,
    'login_rate_window_sec': 60,
    'max_sessions_per_user': 2,
    'timestamps': True,
    'history_size': 50,
    'default_room': 'general',
    'typing_indicator_timeout_sec': 10,
}


def load_config(path: str | None = None) -> dict:
    """Load config from file, merging with defaults."""
    p = path or CONFIG_PATH
    if os.path.exists(p):
        with open(p, 'r') as f:
            cfg = json.load(f)
            return {**DEFAULT_CONFIG, **cfg}
    return DEFAULT_CONFIG.copy()
