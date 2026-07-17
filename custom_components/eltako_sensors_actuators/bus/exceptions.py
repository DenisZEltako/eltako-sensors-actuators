from __future__ import annotations


class EltakoBusError(RuntimeError):
    """Base error for the internal ELTAKO bus core."""


class UnsupportedCommandError(EltakoBusError):
    """Raised when a command cannot be encoded safely."""


class InvalidAddressError(EltakoBusError):
    """Raised when an ELTAKO/EnOcean address has an invalid format."""
