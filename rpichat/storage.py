"""User and room operator persistence."""
import json
import os

ROOM_OPS_PATH = 'room_ops.json'


def load_users(config: dict) -> dict[bytes, bytes]:
    """Load user database (username -> bcrypt hash bytes)."""
    path = config.get('user_db', 'users.json')
    if not os.path.exists(path):
        return {}
    try:
        with open(path, 'r') as f:
            data = json.load(f)
    except (json.JSONDecodeError, ValueError):
        return {}  # empty or corrupted file
    if not isinstance(data, dict):
        return {}
    return {u: p.encode() for u, p in data.items()}


def save_users(users: dict, config: dict) -> None:
    """Save user database."""
    path = config.get('user_db', 'users.json')
    serializable = {u: h.decode() for u, h in users.items()}
    with open(path, 'w') as f:
        json.dump(serializable, f, indent=2)


def load_room_ops(path: str = ROOM_OPS_PATH) -> dict[str, set[str]]:
    """Load room operators (room -> set of usernames)."""
    if not os.path.exists(path):
        return {}
    try:
        with open(path, 'r') as f:
            data = json.load(f)
    except (json.JSONDecodeError, ValueError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {r: set(ops) for r, ops in data.items()}


def save_room_ops(room_ops: dict[str, set[str]], path: str = ROOM_OPS_PATH) -> None:
    """Save room operators."""
    data = {r: list(ops) for r, ops in room_ops.items()}
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
