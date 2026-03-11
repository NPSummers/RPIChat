"""Moderation commands: op, deop, kick."""
from rpichat.cogs.base import Cog, Context
from rpichat.utils import DIM, RESET, sys_msg, colored_username


class ModerationCog(Cog):
    name = "Moderation"

    def get_commands(self):
        return {
            "/op": self.cmd_op,
            "/deop": self.cmd_deop,
            "/kick": self.cmd_kick,
        }

    def get_help_lines(self):
        return [
            "  /op <user>   - Make user a room operator (ops only)",
            "  /deop <user> - Remove op (ops only)",
            "  /kick <user> - Kick user from room (ops only)",
        ]

    async def cmd_op(self, ctx: Context, services) -> bool:
        target = ctx.arg(1)
        if not target:
            return False
        if not services.is_room_op(ctx.room, ctx.username):
            ctx.writer.write(f"{DIM}Only room operators can do that{RESET}\r\n{DIM}> {RESET}")
            await ctx.writer.drain()
            return True
        services.add_room_op(ctx.room, target)
        ctx.writer.write(f"{DIM}{target} is now a room operator{RESET}\r\n{DIM}> {RESET}")
        await ctx.writer.drain()
        return True

    async def cmd_deop(self, ctx: Context, services) -> bool:
        target = ctx.arg(1)
        if not target:
            return False
        if not services.is_room_op(ctx.room, ctx.username):
            ctx.writer.write(f"{DIM}Only room operators can do that{RESET}\r\n{DIM}> {RESET}")
            await ctx.writer.drain()
            return True
        await services.remove_room_op(ctx.room, target)
        ctx.writer.write(f"{DIM}{target} is no longer a room operator{RESET}\r\n{DIM}> {RESET}")
        await ctx.writer.drain()
        return True

    async def cmd_kick(self, ctx: Context, services) -> bool:
        target = ctx.arg(1)
        if not target:
            return False
        if not services.is_room_op(ctx.room, ctx.username):
            ctx.writer.write(f"{DIM}Only room operators can do that{RESET}\r\n{DIM}> {RESET}")
            await ctx.writer.drain()
            return True

        target_proc = services.get_process_for_user(target)
        if not target_proc:
            ctx.writer.write(f"{DIM}User not found{RESET}\r\n{DIM}> {RESET}")
            await ctx.writer.drain()
            return True

        import rpichat.state as state
        target_info = state.clients.get(target_proc, {})
        if target_info.get('room') != ctx.room:
            ctx.writer.write(f"{DIM}User is not in this room{RESET}\r\n{DIM}> {RESET}")
            await ctx.writer.drain()
            return True

        try:
            target_proc.stdout.write(
                f"\r{DIM}You were kicked from {ctx.room} by {ctx.username}{RESET}\r\n"
            )
            await target_proc.stdout.drain()
        except Exception:
            pass

        await services.move_user_to_room(target_proc, ctx.default_room)
        await services.broadcast_to_room(
            ctx.room,
            sys_msg(f'{colored_username(target)} was kicked by {colored_username(ctx.username)}')
        )
        ctx.writer.write(f'{DIM}> {RESET}')
        await ctx.writer.drain()
        return True
