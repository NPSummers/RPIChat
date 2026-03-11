# chat_server.py
import asyncio
import hashlib
import json
import os
import bcrypt
import asyncssh
from asyncssh import SSHServer, SSHServerProcess

# ================= CONFIG =================
PORT = 2022
# ANSI 256-color palette (distinct, readable colors for usernames)
USER_COLORS = [31, 32, 33, 34, 35, 36, 91, 92, 93, 94, 95, 96, 130, 136, 166, 208]
RESET = '\033[0m'
DIM = '\033[2m'
BOLD = '\033[1m'
HOST_KEY = 'ssh_host_key'           # will be generated if missing
USER_DB = 'users.json'
# ===========================================

clients = {}          # session -> username
clients_lock = None   # set in main()
broadcast_queue = None  # set in main()

def load_users():
    if not os.path.exists(USER_DB):
        return {}
    with open(USER_DB, 'r') as f:
        data = json.load(f)
    return {u: p.encode() for u, p in data.items()}  # hashes stored as str, need bytes


def save_users(users):
    # Store only the hash (bytes → base64 str for json)
    serializable = {u: h.decode() for u, h in users.items()}
    with open(USER_DB, 'w') as f:
        json.dump(serializable, f, indent=2)


def color_for_user(username: str) -> str:
    """Return ANSI color code for username (consistent per user)."""
    h = int(hashlib.md5(username.encode()).hexdigest(), 16)
    idx = h % len(USER_COLORS)
    return f'\033[38;5;{USER_COLORS[idx]}m'


def colored_username(username: str) -> str:
    """Username with hash-based color."""
    return f'{color_for_user(username)}{username}{RESET}'


def sys_msg(text: str) -> str:
    """System message styling."""
    return f'{DIM}*** {text} ***{RESET}'


class ChatServer(SSHServer):
    def __init__(self):
        super().__init__()
        self.users = load_users()
        self.username = None

    def connection_made(self, conn):
        print(f"New connection from {conn.get_extra_info('peername')[0]}")

    def begin_auth(self, username: str) -> bool:
        self.username = username.strip()
        if not self.username:
            return False
        return True  # We'll handle auth ourselves

    def public_key_auth_supported(self) -> bool:
        return False  # password only — avoids client waiting on public key

    def password_auth_supported(self) -> bool:
        return True

    def validate_password(self, username: str, password: str) -> bool:
        pw_bytes = password.encode()

        if password == "register":
            if username in self.users:
                return False  # already exists → reject register
            return True  # let them in, then force set password

        # Normal login
        if username in self.users:
            if bcrypt.checkpw(pw_bytes, self.users[username]):
                return True

        return False

    async def start_session(self, process: SSHServerProcess) -> None:
        if process.channel.get_command():
            # No exec/command support — only shell
            process.exit(1)
            return

        await self.interactive_shell(process)

    async def interactive_shell(self, process: SSHServerProcess):
        writer = process.stdout
        reader = process.stdin

        username = self.username

        # Special case: just registered
        if username not in self.users:
            writer.write('\r\nCreating new account...\r\n')
            await writer.drain()
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
            async with clients_lock:
                self.users[username] = hashed
            save_users(self.users)
            writer.write(f'\r\n{DIM}Account created!{RESET} {BOLD}Welcome!{RESET}\r\n\r\n')
        else:
            writer.write(f'\r\nWelcome back, {colored_username(username)}!\r\n\r\n')
        await writer.drain()

        # Join chat
        async with clients_lock:
            clients[process] = username

        await broadcast(sys_msg(f'{colored_username(username)} has joined the chat'))

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

                if msg == '/who':
                    async with clients_lock:
                        names = sorted(clients.values())
                    colored = ', '.join(colored_username(n) for n in names)
                    writer.write(f"{DIM}Online:{RESET} {colored}\r\n{DIM}> {RESET}")
                    await writer.drain()
                    continue

                if msg.startswith('/'):
                    writer.write(f"{DIM}Unknown command. Try /who or /exit{RESET}\r\n{DIM}> {RESET}")
                    await writer.drain()
                    continue

                await broadcast(f"<{colored_username(username)}> {msg}")
                writer.write(f'{DIM}> {RESET}')
                await writer.drain()

        except asyncssh.misc.ChannelOpenError:
            pass
        except Exception as e:
            print(f"Error in shell: {e}")

        # Cleanup
        async with clients_lock:
            if process in clients:
                del clients[process]

        await broadcast(sys_msg(f'{colored_username(username)} has left the chat'))
        process.exit(0)

    async def _read_password(self, reader, writer):
        writer.write('\x1b[?25l')  # hide cursor (optional)
        await writer.drain()
        pw = ''
        while True:
            c = await reader.readexactly(1)
            if c in ('\r', '\n'):
                writer.write('\r\n')
                await writer.drain()
                break
            if c == '\x7f' and pw:  # backspace
                pw = pw[:-1]
                writer.write('\b \b')
            elif c and ord(c) >= 32 and ord(c) <= 126:  # printable ASCII
                pw += c
                writer.write('*')
            await writer.drain()
        writer.write('\x1b[?25h')  # show cursor
        await writer.drain()
        return pw.strip()

    def connection_lost(self, exc):
        if exc:
            print(f"Connection lost: {exc}")


async def broadcaster():
    while True:
        msg = await broadcast_queue.get()
        line = f"\r{msg}\r\n{DIM}> {RESET}"
        async with clients_lock:
            for proc in list(clients):
                if not proc.is_closing():
                    try:
                        proc.stdout.write(line)
                        await proc.stdout.drain()
                    except:
                        pass


async def broadcast(msg: str):
    if broadcast_queue is not None:
        await broadcast_queue.put(msg)


async def main():
    global broadcast_queue, clients_lock
    broadcast_queue = asyncio.Queue()
    clients_lock = asyncio.Lock()

    if not os.path.exists(HOST_KEY):
        print("Generating host key...")
        os.system(f"ssh-keygen -t ed25519 -f {HOST_KEY} -N '' -q")

    async def process_factory(proc):
        conn = proc.channel.get_connection()
        server = conn.get_owner()
        if isinstance(server, ChatServer):
            await server.start_session(proc)

    server = await asyncssh.create_server(
        ChatServer,
        '',
        PORT,
        server_host_keys=[HOST_KEY],
        process_factory=process_factory,
        encoding='utf-8',
        line_editor=True,  # required for PTY input to work
        line_echo=True
    )

    print(f"Chat server listening on port {PORT} ...")

    asyncio.create_task(broadcaster())

    await server.serve_forever()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped.")