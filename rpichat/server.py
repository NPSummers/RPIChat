"""SSH chat server and session handling."""
import asyncio
import time
import bcrypt
import asyncssh
from asyncssh import SSHServer, SSHServerProcess
from collections import deque

from rpichat.config import load_config
from rpichat.storage import load_users, save_users, save_room_ops
import rpichat.state as state
from rpichat.utils import (
    RESET,
    DIM,
    BOLD,
    valid_username,
    colored_username,
    sys_msg,
    fmt_msg,
)
from rpichat.cogs import CommandRegistry, CommandServices, load_cogs
from rpichat.cogs.base import Context

config = load_config()


def _count_user_sessions(username: str) -> int:
    return sum(1 for c in state.clients.values() if c.get('username') == username)


async def broadcast_to_room(room: str, msg: str, exclude_process=None) -> None:
    if state.broadcast_queue is not None:
        await state.broadcast_queue.put((room, msg, exclude_process))


async def _append_history(room: str, msg: str) -> None:
    size = config.get('history_size', 50)
    async with state.room_history_lock:
        if room not in state.room_history:
            state.room_history[room] = deque(maxlen=size)
        state.room_history[room].append((time.time(), msg))


async def _get_history(room: str) -> list:
    async with state.room_history_lock:
        hist = state.room_history.get(room, deque())
        return list(hist)


async def broadcaster() -> None:
    while True:
        item = await state.broadcast_queue.get()
        if isinstance(item, tuple):
            room, msg, exclude = item[0], item[1], item[2] if len(item) > 2 else None
        else:
            room, msg, exclude = 'general', item, None
        line = f"\r{msg}\r\n{DIM}> {RESET}"
        async with state.clients_lock:
            for proc, info in list(state.clients.items()):
                if info.get('room') == room and not proc.is_closing() and proc != exclude:
                    try:
                        proc.stdout.write(line)
                        await proc.stdout.drain()
                    except Exception:
                        pass


def _create_registry_and_services(read_password_fn) -> tuple[CommandRegistry, CommandServices]:
    registry = CommandRegistry()
    for cog in load_cogs():
        registry.add_cog(cog)

    services = CommandServices(
        config=config,
        broadcast_fn=broadcast_to_room,
        read_password_fn=read_password_fn,
        get_help_text_fn=registry.get_help_text,
    )
    return registry, services


class ChatServer(SSHServer):
    def __init__(self):
        super().__init__()
        self.users = load_users(config)
        self.username = None

    def connection_made(self, conn):
        self.conn = conn
        self.peer_ip = conn.get_extra_info('peername', ('?',))[0]
        print(f"New connection from {self.peer_ip}")

    async def _check_rate_limit(self) -> bool:
        limit = config.get('login_rate_limit', 5)
        window = config.get('login_rate_window_sec', 60)
        now = time.time()
        async with state.login_attempts_lock:
            key = self.peer_ip
            if key not in state.login_attempts:
                state.login_attempts[key] = []
            attempts = state.login_attempts[key]
            attempts[:] = [t for t in attempts if now - t < window]
            if len(attempts) >= limit:
                return False
            attempts.append(now)
            return True

    async def _record_auth_success(self) -> None:
        async with state.login_attempts_lock:
            key = self.peer_ip
            if key in state.login_attempts:
                state.login_attempts[key] = []

    async def begin_auth(self, username: str) -> bool:
        if not await self._check_rate_limit():
            return False
        if config.get('login_banner'):
            self.conn.send_auth_banner(config['login_banner'])
        self.username = username.strip()
        if not self.username:
            return False
        return True

    def public_key_auth_supported(self) -> bool:
        return False

    def password_auth_supported(self) -> bool:
        return True

    async def validate_password(self, username: str, password: str) -> bool:
        pw_bytes = password.encode()
        if password == "register":
            if username in self.users:
                return False
            if not valid_username(username, config)[0]:
                return False
            return True
        if username in self.users:
            if bcrypt.checkpw(pw_bytes, self.users[username]):
                await self._record_auth_success()
                return True
        return False

    async def start_session(self, process: SSHServerProcess) -> None:
        if process.channel.get_command():
            process.exit(1)
            return
        await self.interactive_shell(process)

    async def interactive_shell(self, process: SSHServerProcess) -> None:
        writer = process.stdout
        reader = process.stdin
        username = self.username
        default_room = config.get('default_room', 'general')
        room_container = [default_room]

        registry, services = _create_registry_and_services(self._read_password)

        max_sess = config.get('max_sessions_per_user', 2)
        if _count_user_sessions(username) >= max_sess:
            writer.write(f'\r\n{DIM}Too many sessions. Max {max_sess} per user.{RESET}\r\n')
            await writer.drain()
            process.exit(1)
            return

        if username not in self.users:
            writer.write('\r\nCreating new account...\r\n')
            await writer.drain()
            ok, err = valid_username(username, config)
            if not ok:
                writer.write(f'\r\n{DIM}{err}{RESET}\r\n')
                await writer.drain()
                process.exit(1)
                return
            while True:
                writer.write('Set your password: ')
                await writer.drain()
                pw1 = await self._read_password(reader, writer)
                if not pw1:
                    writer.write('\r\nAborted.\r\n')
                    await writer.drain()
                    process.exit(1)
                    return
                writer.write('\r\nConfirm password: ')
                await writer.drain()
                pw2 = await self._read_password(reader, writer)
                if pw1 == pw2 and len(pw1) >= 4:
                    break
                writer.write('\r\nPasswords do not match or too short. Try again.\r\n')
                await writer.drain()
            hashed = bcrypt.hashpw(pw1.encode(), bcrypt.gensalt())
            async with state.clients_lock:
                self.users[username] = hashed
            save_users(self.users, config)
            writer.write(f'\r\n{DIM}Account created!{RESET}\r\n{BOLD}Welcome to RPIChat {colored_username(username)}!{RESET}\r\n\r\n')
        else:
            writer.write(f'\r\n{BOLD}Welcome to RPIChat {colored_username(username)}!{RESET}\r\n\r\n')
        await writer.drain()

        room = room_container[0]
        async with state.clients_lock:
            state.clients[process] = {"username": username, "room": room}

        await broadcast_to_room(room, sys_msg(f'{colored_username(username)} has joined the chat'))
        await _append_history(room, sys_msg(f'{username} has joined the chat'))

        hist = await _get_history(room)
        history_size = config.get('history_size', 50)
        for ts, hmsg in hist[-history_size:]:
            if config.get('timestamps'):
                t = time.strftime('%H:%M', time.localtime(ts))
                writer.write(f"{DIM}[{t}]{RESET} {hmsg}\r\n")
            else:
                writer.write(f"{hmsg}\r\n")
            await writer.drain()

        writer.write(f'{DIM}> {RESET}')
        await writer.drain()

        try:
            while not process.is_closing():
                line = await reader.readline()
                msg = line.rstrip('\r\n') if line else ''

                if not msg:
                    writer.write(f'{DIM}> {RESET}')
                    await writer.drain()
                    continue

                if msg.lower() in ('/exit', '/quit'):
                    break

                room = room_container[0]
                if msg.startswith('/'):
                    parts = msg.split()
                    cmd_key = parts[0].lower()
                    handler = registry.get_handler(cmd_key)
                    if handler:
                        ctx = Context(
                            writer=writer,
                            reader=reader,
                            process=process,
                            username=username,
                            room=room,
                            msg=msg,
                            args=parts,
                            config=config,
                            users=self.users,
                            default_room=default_room,
                        )
                        try:
                            handled = await handler(ctx, services)
                            if handled and hasattr(ctx, 'room'):
                                room_container[0] = ctx.room
                        except Exception as e:
                            print(f"Command error: {e}")
                            writer.write(f"{DIM}Error executing command.{RESET}\r\n{DIM}> {RESET}")
                            await writer.drain()
                    else:
                        writer.write(f"{DIM}Unknown command. /help for list{RESET}\r\n{DIM}> {RESET}")
                        await writer.drain()
                    continue

                full = fmt_msg(f"<{colored_username(username)}> {msg}", config)
                await broadcast_to_room(room, full)
                await _append_history(room, f"<{username}> {msg}")
                writer.write(f'{DIM}> {RESET}')
                await writer.drain()

        except asyncssh.misc.ChannelOpenError:
            pass
        except Exception as e:
            print(f"Error in shell: {e}")

        async with state.clients_lock:
            if process in state.clients:
                info = state.clients[process]
                room = info.get('room', default_room)
                del state.clients[process]

        await broadcast_to_room(room, sys_msg(f'{colored_username(username)} has left the chat'))
        await _append_history(room, sys_msg(f'{username} has left the chat'))
        process.exit(0)

    async def _read_password(self, reader, writer) -> str:
        writer.write('\x1b[?25l')
        await writer.drain()
        pw = ''
        while True:
            c = await reader.readexactly(1)
            if c in ('\r', '\n'):
                writer.write('\r\n')
                await writer.drain()
                break
            if c == '\x7f' and pw:
                pw = pw[:-1]
                writer.write('\b \b')
            elif c and 32 <= ord(c) <= 126:
                pw += c
                writer.write('*')
            await writer.drain()
        writer.write('\x1b[?25h')
        await writer.drain()
        return pw.strip()

    def connection_lost(self, exc):
        if exc:
            print(f"Connection lost: {exc}")
