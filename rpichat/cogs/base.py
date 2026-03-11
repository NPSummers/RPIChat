"""Cog base class and command context."""
from dataclasses import dataclass
from typing import Any


@dataclass
class Context:
    """Context passed to every command handler."""
    writer: Any
    reader: Any
    process: Any
    username: str
    room: str
    msg: str
    args: list[str]
    config: dict
    users: dict  # user db (username -> hash)
    default_room: str

    @property
    def cmd(self) -> str:
        """The command name (e.g. 'help'), or empty if not a command."""
        if self.msg.startswith('/') and self.args:
            return self.args[0].lower()
        return ''

    def arg(self, i: int, default: str = '') -> str:
        """Get arg at index (0 = command name)."""
        try:
            return self.args[i]
        except IndexError:
            return default

    def rest(self, from_arg: int = 1) -> str:
        """Get remaining message from arg index onward."""
        return ' '.join(self.args[from_arg:]) if len(self.args) > from_arg else ''


class Cog:
    """Base class for command cogs. Override get_commands() and get_help_lines()."""

    name: str = "Base"

    def get_commands(self) -> dict[str, callable]:
        """Return {"/cmdname": async_handler, ...}. Handler receives (ctx, services)."""
        return {}

    def get_help_lines(self) -> list[str]:
        """Return help lines for /help. Example: ["  /cmd - description"]"""
        return []
