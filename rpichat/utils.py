"""Formatting, colors, and validation utilities."""
import hashlib
import re
import time

USER_COLORS = [31, 32, 33, 34, 35, 36, 91, 92, 93, 94, 95, 96, 130, 136, 166, 208]
RESET = '\033[0m'
DIM = '\033[2m'
BOLD = '\033[1m'
CLEAR = '\033[2J\033[H'


def valid_username(name: str, config: dict) -> tuple[bool, str]:
    """Return (valid, error_msg)."""
    min_len = config.get('username_min_len', 3)
    max_len = config.get('username_max_len', 20)
    if len(name) < min_len:
        return False, f"Username must be at least {min_len} characters"
    if len(name) > max_len:
        return False, f"Username must be at most {max_len} characters"
    if not re.match(r'^[a-zA-Z0-9_-]+$', name):
        return False, "Username can only contain letters, numbers, underscore, hyphen"
    return True, ""


def color_for_user(username: str) -> str:
    """ANSI color code for username (consistent per user)."""
    h = int(hashlib.md5(username.encode()).hexdigest(), 16)
    idx = h % len(USER_COLORS)
    return f'\033[38;5;{USER_COLORS[idx]}m'


def colored_username(username: str) -> str:
    """Username with hash-based color."""
    return f'{color_for_user(username)}{username}{RESET}'


def sys_msg(text: str) -> str:
    """System message styling."""
    return f'{DIM}*** {text} ***{RESET}'


def fmt_msg(msg: str, config: dict, prefix: str = "") -> str:
    """Format message with optional timestamp."""
    if config.get('timestamps', False):
        t = time.strftime('%H:%M', time.localtime())
        return f"{prefix}[{t}] {msg}"
    return f"{prefix}{msg}"


HELP_TEXT = f"""
{DIM}Commands:{RESET}
  /help          - Show this help
  /online        - List users in this room
  /join <room>   - Join or create a room (e.g. /join #general)
  /rooms         - List available rooms
  /msg <user> <message> - Send a private message
  /me <action>   - Action (e.g. /me waves)
  /clear         - Clear your screen
  /changepass    - Change your password
  /op <user>     - Make user a room operator (ops only)
  /kick <user>   - Kick user from room (ops only)
  /deop <user>   - Remove op (ops only)
  /typing        - Show "you are typing..." to others
  /exit, /quit   - Disconnect
"""
