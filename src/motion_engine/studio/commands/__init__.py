"""Command registry for menus, shortcuts, and toolbar actions."""

from motion_engine.studio.commands.builtin import register_builtin_commands
from motion_engine.studio.commands.command import Command
from motion_engine.studio.commands.registry import CommandRegistry

__all__ = [
    "Command",
    "CommandRegistry",
    "register_builtin_commands",
]
