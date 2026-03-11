"""General commands: help, online, rooms, clear."""
from rpichat.cogs.base import Cog, Context
from rpichat.utils import DIM, RESET, CLEAR, colored_username


class GeneralCog(Cog):
    name = "General"

    def get_commands(self):
        return {
            "/help": self.cmd_help,
            "/online": self.cmd_online,
            "/rooms": self.cmd_rooms,
            "/clear": self.cmd_clear,
        }

    def get_help_lines(self):
        return [
            "  /help   - Show this help",
            "  /online - List users in this room",
            "  /rooms  - List available rooms",
            "  /clear  - Clear your screen",
            "  /exit, /quit - Disconnect",
        ]

    async def cmd_help(self, ctx: Context, services) -> bool:
        ctx.writer.write(services.get_help_text())
        ctx.writer.write(f"{DIM}> {RESET}")
        await ctx.writer.drain()
        return True

    async def cmd_online(self, ctx: Context, services) -> bool:
        in_room = await services.get_users_in_room(ctx.room)
        colored = ', '.join(colored_username(n) for n in sorted(in_room))
        ctx.writer.write(f"{DIM}Online:{RESET} {colored}\r\n{DIM}> {RESET}")
        await ctx.writer.drain()
        return True

    async def cmd_rooms(self, ctx: Context, services) -> bool:
        rooms = await services.get_all_rooms()
        ctx.writer.write(f"{DIM}Rooms:{RESET} {', '.join(sorted(rooms))}\r\n{DIM}> {RESET}")
        await ctx.writer.drain()
        return True

    async def cmd_clear(self, ctx: Context, services) -> bool:
        ctx.writer.write(CLEAR)
        ctx.writer.write(f"{DIM}> {RESET}")
        await ctx.writer.drain()
        return True
