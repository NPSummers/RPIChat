# Cogs - Pluggable Commands

Cogs let you add new commands without editing the main server.

## Adding a New Command

1. **Create a new cog file** in `rpichat/cogs/`, e.g. `rpichat/cogs/greeting.py`:

```python
"""Greeting commands."""
from rpichat.cogs.base import Cog, Context
from rpichat.utils import DIM, RESET


class GreetingCog(Cog):
    name = "Greeting"

    def get_commands(self):
        return {
            "/hello": self.cmd_hello,
            "/greet": self.cmd_greet,
        }

    def get_help_lines(self):
        return [
            "  /hello - Say hello",
            "  /greet <name> - Greet someone",
        ]

    async def cmd_hello(self, ctx: Context, services) -> bool:
        ctx.writer.write("Hello!\r\n")
        ctx.writer.write(f"{DIM}> {RESET}")
        await ctx.writer.drain()
        return True

    async def cmd_greet(self, ctx: Context, services) -> bool:
        name = ctx.arg(1) or "everyone"
        await services.broadcast_to_room(ctx.room, f"* {ctx.username} greets {name}")
        ctx.writer.write(f"{DIM}> {RESET}")
        await ctx.writer.drain()
        return True
```

2. **Register the cog** in `rpichat/cogs/__init__.py`:

```python
def load_cogs() -> list[Cog]:
    from rpichat.cogs.general import GeneralCog
    from rpichat.cogs.rooms import RoomsCog
    from rpichat.cogs.messages import MessagesCog
    from rpichat.cogs.moderation import ModerationCog
    from rpichat.cogs.account import AccountCog
    from rpichat.cogs.greeting import GreetingCog  # add this
    return [
        GeneralCog(),
        RoomsCog(),
        MessagesCog(),
        ModerationCog(),
        AccountCog(),
        GreetingCog(),  # add this
    ]
```

## Context

Each handler receives `(ctx: Context, services: CommandServices)`:

- **ctx.writer** / **ctx.reader** - I/O streams
- **ctx.process** - SSH process
- **ctx.username** - Your username
- **ctx.room** - Current room (assign to change room in /join)
- **ctx.msg** - Full message string
- **ctx.args** - Split words (e.g. `["/msg", "alice", "hi"]`)
- **ctx.arg(i)** - Get arg at index
- **ctx.rest(from_arg)** - Remaining text from arg onward
- **ctx.config** - Server config
- **ctx.users** - User DB (for account commands)
- **ctx.default_room** - Default room name

## Services

- **services.broadcast_to_room(room, msg)** - Send to room
- **services.append_history(room, msg)** - Add to history
- **services.get_history(room)** - Get room history
- **services.get_users_in_room(room)** - Users in room
- **services.get_all_rooms()** - All room names
- **services.switch_room(process, username, old, new)** - Move user
- **services.get_process_for_user(username)** - Find user's process
- **services.is_room_op(room, username)** - Check op status
- **services.add_room_op(room, username)** - Grant op
- **services.remove_room_op(room, username)** - Remove op
- **services.read_password(reader, writer)** - Read masked password

## Return Value

Return `True` if the command was handled, `False` to fall through (rare).
