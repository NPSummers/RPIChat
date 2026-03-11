"""Cogs - pluggable command modules."""
from rpichat.cogs.base import Cog, Context
from rpichat.cogs.registry import CommandRegistry
from rpichat.cogs.services import CommandServices


def load_cogs() -> list[Cog]:
    """Return list of default cog instances."""
    from rpichat.cogs.general import GeneralCog
    from rpichat.cogs.rooms import RoomsCog
    from rpichat.cogs.messages import MessagesCog
    from rpichat.cogs.moderation import ModerationCog
    from rpichat.cogs.account import AccountCog
    return [
        GeneralCog(),
        RoomsCog(),
        MessagesCog(),
        ModerationCog(),
        AccountCog(),
    ]


__all__ = ['Cog', 'Context', 'CommandRegistry', 'CommandServices', 'load_cogs']
