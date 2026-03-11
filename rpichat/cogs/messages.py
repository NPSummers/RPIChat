"""Message commands: msg, me, typing."""
from rpichat.cogs.base import Cog, Context
from rpichat.utils import DIM, RESET, sys_msg, colored_username, fmt_msg


class MessagesCog(Cog):
    name = "Messages"

    def get_commands(self):
        return {
            "/msg": self.cmd_msg,
            "/me": self.cmd_me,
            "/typing": self.cmd_typing,
        }

    def get_help_lines(self):
        return [
            "  /msg <user> <message> - Send a private message",
            "  /me <action> - Action (e.g. /me waves)",
            "  /typing - Show typing indicator to others",
        ]

    async def cmd_msg(self, ctx: Context, services) -> bool:
        if len(ctx.args) < 3:
            ctx.writer.write(f"{DIM}Usage: /msg <user> <message>{RESET}\r\n{DIM}> {RESET}")
            await ctx.writer.drain()
            return True

        target = ctx.arg(1)
        rest = ctx.rest(2)
        target_proc = services.get_process_for_user(target, exclude_process=ctx.process)
        if not target_proc:
            ctx.writer.write(f"{DIM}User not found or offline{RESET}\r\n{DIM}> {RESET}")
            await ctx.writer.drain()
            return True

        dm = f"{DIM}[DM from {colored_username(ctx.username)}]{DIM} {rest}"
        try:
            target_proc.stdout.write(f"\r{dm}\r\n{DIM}> {RESET}")
            await target_proc.stdout.drain()
        except Exception:
            pass
        ctx.writer.write(f"{DIM}[DM to {colored_username(target)}]{RESET} {rest}\r\n{DIM}> {RESET}")
        await ctx.writer.drain()
        return True

    async def cmd_me(self, ctx: Context, services) -> bool:
        action = ctx.rest(1)
        if not action:
            return False
        full = fmt_msg(f"* {colored_username(ctx.username)} {action}", ctx.config)
        await services.broadcast_to_room(ctx.room, full)
        await services.append_history(ctx.room, f"* {ctx.username} {action}")
        ctx.writer.write(f'{DIM}> {RESET}')
        await ctx.writer.drain()
        return True

    async def cmd_typing(self, ctx: Context, services) -> bool:
        await services.set_typing(ctx.room, ctx.username)
        await services.broadcast_to_room(
            ctx.room,
            sys_msg(f'{colored_username(ctx.username)} is typing...'),
            exclude_process=ctx.process
        )
        ctx.writer.write(f'{DIM}> {RESET}')
        await ctx.writer.drain()
        return True
