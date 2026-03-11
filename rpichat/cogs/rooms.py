"""Room commands: join."""
from rpichat.cogs.base import Cog, Context
from rpichat.utils import DIM, RESET, sys_msg, colored_username


class RoomsCog(Cog):
    name = "Rooms"

    def get_commands(self):
        return {"/join": self.cmd_join}

    def get_help_lines(self):
        return ["  /join <room> - Join or create a room (e.g. /join #general)"]

    async def cmd_join(self, ctx: Context, services) -> bool:
        new_room = ctx.rest(1).strip().lstrip('#')
        if not new_room:
            ctx.writer.write(f"{DIM}Usage: /join <room>{RESET}\r\n{DIM}> {RESET}")
            await ctx.writer.drain()
            return True

        room = ctx.room
        await services.switch_room(ctx.process, ctx.username, room, new_room)
        ctx.room = new_room  # update for caller

        await services.broadcast_to_room(new_room, sys_msg(f'{colored_username(ctx.username)} has joined the chat'))
        await services.append_history(new_room, sys_msg(f'{ctx.username} has joined the chat'))

        hist = await services.get_history(new_room)
        history_size = ctx.config.get('history_size', 50)
        for ts, hmsg in hist[-history_size:]:
            if ctx.config.get('timestamps'):
                import time
                t = time.strftime('%H:%M', time.localtime(ts))
                ctx.writer.write(f"{DIM}[{t}]{RESET} {hmsg}\r\n")
            else:
                ctx.writer.write(f"{hmsg}\r\n")
            await ctx.writer.drain()

        ctx.writer.write(f"{DIM}Joined {new_room}{RESET}\r\n{DIM}> {RESET}")
        await ctx.writer.drain()
        return True
