# Prevent circular imports by importing is_authorized after other imports
from internal.commands.system_commands import is_authorized_global, is_authorized_server

__all__ = ['is_authorized_global', 'is_authorized_server']