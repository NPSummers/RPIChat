"""Runtime state: clients, rooms, locks, broadcast queue."""
import asyncio
from collections import deque
from typing import Any

clients: dict[Any, dict] = {}
clients_lock: asyncio.Lock = None  # type: ignore
broadcast_queue: asyncio.Queue | None = None
room_history: dict[str, deque] = {}
room_history_lock: asyncio.Lock = None  # type: ignore
room_ops: dict[str, set[str]] = {}
room_ops_lock: asyncio.Lock = None  # type: ignore
login_attempts: dict[str, list[float]] = {}
login_attempts_lock: asyncio.Lock = None  # type: ignore
typing_users: dict[str, dict[str, float]] = {}
typing_lock: asyncio.Lock = None  # type: ignore


def init_state(config: dict) -> None:
    """Initialize all locks and load room_ops."""
    global clients_lock, broadcast_queue, room_history_lock
    global room_ops_lock, login_attempts_lock, typing_lock, room_ops

    from rpichat.storage import load_room_ops as load_room_ops_storage

    broadcast_queue = asyncio.Queue()
    clients_lock = asyncio.Lock()
    room_history_lock = asyncio.Lock()
    room_ops_lock = asyncio.Lock()
    login_attempts_lock = asyncio.Lock()
    typing_lock = asyncio.Lock()
    room_ops.clear()
    room_ops.update(load_room_ops_storage())
