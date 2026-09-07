"""Persistent water-filter replacement tracking."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.storage import Store

from .const import DOMAIN

STORAGE_VERSION = 1


class WaterFilterTracker:
    """Store and publish the last water-filter replacement time."""

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        self._store: Store[dict[str, str]] = Store(
            hass, STORAGE_VERSION, f"{DOMAIN}.{entry_id}.water_filter"
        )
        self._listeners: set[Callable[[], None]] = set()
        self.last_replaced: datetime | None = None

    async def async_load(self) -> None:
        """Load the stored timestamp or initialize it on first setup."""
        stored = await self._store.async_load()
        if stored is not None and (value := stored.get("last_replaced")):
            try:
                parsed = datetime.fromisoformat(value)
            except ValueError:
                pass
            else:
                if parsed.tzinfo is not None:
                    self.last_replaced = parsed
                    return

        await self.async_reset()

    async def async_reset(self) -> None:
        """Set the replacement time to now and persist it."""
        self.last_replaced = datetime.now(UTC)
        await self._store.async_save({"last_replaced": self.last_replaced.isoformat()})
        for listener in tuple(self._listeners):
            listener()

    @callback
    def async_add_listener(self, listener: Callable[[], None]) -> Callable[[], None]:
        """Register a callback for timestamp changes."""
        self._listeners.add(listener)

        @callback
        def remove_listener() -> None:
            self._listeners.discard(listener)

        return remove_listener
