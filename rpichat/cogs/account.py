"""Account commands: changepass."""
import bcrypt

import rpichat.state as state
from rpichat.cogs.base import Cog, Context
from rpichat.utils import DIM, RESET
from rpichat.storage import save_users


class AccountCog(Cog):
    name = "Account"

    def get_commands(self):
        return {"/changepass": self.cmd_changepass}

    def get_help_lines(self):
        return ["  /changepass - Change your password"]

    async def cmd_changepass(self, ctx: Context, services) -> bool:
        ctx.writer.write('Current password: ')
        await ctx.writer.drain()
        old_pw = await services.read_password(ctx.reader, ctx.writer)
        if not bcrypt.checkpw(old_pw.encode(), ctx.users[ctx.username]):
            ctx.writer.write(f'\r\n{DIM}Wrong password.{RESET}\r\n{DIM}> {RESET}')
            await ctx.writer.drain()
            return True

        ctx.writer.write('\r\nNew password: ')
        await ctx.writer.drain()
        pw1 = await services.read_password(ctx.reader, ctx.writer)
        ctx.writer.write('\r\nConfirm new password: ')
        await ctx.writer.drain()
        pw2 = await services.read_password(ctx.reader, ctx.writer)
        if pw1 != pw2 or len(pw1) < 4:
            ctx.writer.write(f'\r\n{DIM}Passwords do not match or too short.{RESET}\r\n{DIM}> {RESET}')
            await ctx.writer.drain()
            return True

        hashed = bcrypt.hashpw(pw1.encode(), bcrypt.gensalt())
        async with state.clients_lock:
            ctx.users[ctx.username] = hashed
        save_users(ctx.users, ctx.config)
        ctx.writer.write(f'\r\n{DIM}Password changed.{RESET}\r\n{DIM}> {RESET}')
        await ctx.writer.drain()
        return True
