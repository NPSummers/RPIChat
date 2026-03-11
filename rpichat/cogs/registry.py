"""Command registry - loads cogs and dispatches commands."""
from typing import Any

from rpichat.cogs.base import Context, Cog
from rpichat.utils import DIM, RESET


class CommandRegistry:
    """Collects cogs and dispatches commands."""

    def __init__(self):
        self._commands: dict[str, callable] = {}
        self._help_lines: list[str] = []
        self._aliases: dict[str, str] = {}  # alias -> canonical

    def add_cog(self, cog: Cog) -> None:
        """Register a cog's commands and help."""
        for cmd, handler in cog.get_commands().items():
            self._commands[cmd.lower()] = handler
        self._help_lines.extend(cog.get_help_lines())

    def add_alias(self, alias: str, target: str) -> None:
        """Add command alias, e.g. add_alias('/q', '/quit')."""
        self._aliases[alias.lower()] = target.lower()

    def get_handler(self, cmd: str):
        """Get handler for command, resolving aliases."""
        cmd = cmd.lower()
        if cmd in self._aliases:
            cmd = self._aliases[cmd]
        return self._commands.get(cmd)

    def get_help_text(self) -> str:
        """Full /help output."""
        lines = '\n'.join(sorted(set(self._help_lines)))
        return f"\n{DIM}Commands:{RESET}\n{lines}\n"

    def all_commands(self) -> set[str]:
        """Set of all registered command names."""
        return set(self._commands.keys()) | set(self._aliases.keys())
