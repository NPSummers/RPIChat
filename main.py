#!/usr/bin/env python3
"""Entry point for RPIChat server."""
import asyncio
import os
import signal

import asyncssh

from rpichat.config import load_config
from rpichat.server import ChatServer, broadcaster
from rpichat.state import init_state


async def main() -> None:
    config = load_config()
    init_state(config)

    port = config['port']
    host_key = config['host_key']
    if not os.path.exists(host_key):
        print("Generating host key...")
        os.system(f'ssh-keygen -t ed25519 -f {host_key} -N "" -q')

    async def process_factory(proc):
        conn = proc.channel.get_connection()
        server = conn.get_owner()
        if isinstance(server, ChatServer):
            await server.start_session(proc)

    server = await asyncssh.create_server(
        ChatServer,
        '',
        port,
        server_host_keys=[host_key],
        process_factory=process_factory,
        encoding='utf-8',
        line_editor=True,
        line_echo=True,
    )

    print(f"Chat server listening on port {port} ...")

    asyncio.create_task(broadcaster())

    loop = asyncio.get_running_loop()
    stop = asyncio.Future()

    def shutdown():
        if not stop.done():
            stop.set_result(None)

    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, shutdown)
        except (ValueError, OSError, NotImplementedError):
            pass  # signal handlers not available (e.g. on Windows)

    server_task = asyncio.create_task(server.serve_forever())
    try:
        await asyncio.wait([server_task, stop], return_when=asyncio.FIRST_COMPLETED)
    finally:
        server.close()
        await server.wait_closed()
        print("Server stopped.")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped.")
