"""Services object - provides helpers to command handlers."""
import time
from collections import deque

import rpichat.state as state
from rpichat.storage import save_room_ops
from rpichat.utils import sys_msg, colored_username


class CommandServices:
    """Injectable services for command handlers."""

    def __init__(self, config, broadcast_fn, read_password_fn, get_help_text_fn=None):
        self.config = config
        self._broadcast = broadcast_fn
        self._read_password = read_password_fn
        self._get_help_text = get_help_text_fn or (lambda: "")
        self.clients_lock = state.clients_lock

    def get_help_text(self) -> str:
        return self._get_help_text()

    async def broadcast_to_room(self, room: str, msg: str, exclude_process=None):
        await self._broadcast(room, msg, exclude_process)

    async def append_history(self, room: str, msg: str):
        size = self.config.get('history_size', 50)
        async with state.room_history_lock:
            if room not in state.room_history:
                state.room_history[room] = deque(maxlen=size)
            state.room_history[room].append((time.time(), msg))

    async def get_history(self, room: str) -> list:
        async with state.room_history_lock:
            hist = state.room_history.get(room, deque())
            return list(hist)

    async def get_users_in_room(self, room: str) -> list[str]:
        async with state.clients_lock:
            return [
                c['username'] for p, c in state.clients.items()
                if c.get('room') == room and not p.is_closing()
            ]

    async def get_all_rooms(self) -> set[str]:
        async with state.clients_lock:
            return set(c.get('room', '') for c in state.clients.values())

    async def switch_room(self, process, username, old_room: str, new_room: str):
        async with state.clients_lock:
            if process in state.clients:
                if old_room != new_room:
                    await self.broadcast_to_room(old_room, sys_msg(f'{colored_username(username)} left the room'))
                    await self.append_history(old_room, sys_msg(f'{username} left the room'))
                state.clients[process]['room'] = new_room
                if new_room not in state.room_ops:
                    self.add_room_op(new_room, username)

    def get_process_for_user(self, username: str, exclude_process=None):
        for proc, info in state.clients.items():
            if info.get('username') == username and proc != exclude_process and not proc.is_closing():
                return proc
        return None

    def is_room_op(self, room: str, username: str) -> bool:
        return username in state.room_ops.get(room, set())

    def add_room_op(self, room: str, username: str):
        if room not in state.room_ops:
            state.room_ops[room] = set()
        state.room_ops[room].add(username)
        save_room_ops(state.room_ops)

    async def remove_room_op(self, room: str, username: str):
        async with state.room_ops_lock:
            if room in state.room_ops:
                state.room_ops[room].discard(username)
                save_room_ops(state.room_ops)

    async def move_user_to_room(self, process, room: str):
        async with state.clients_lock:
            if process in state.clients:
                state.clients[process]['room'] = room

    async def set_typing(self, room: str, username: str):
        async with state.typing_lock:
            if room not in state.typing_users:
                state.typing_users[room] = {}
            timeout = self.config.get('typing_indicator_timeout_sec', 10)
            state.typing_users[room][username] = time.time() + timeout

    async def read_password(self, reader, writer) -> str:
        return await self._read_password(reader, writer)
