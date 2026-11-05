"""One coordinator per API resource: one request per resource and per cycle."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import MeteoKouranError, async_fetch
from .const import CONF_URL, SCAN_INTERVALS

_LOGGER = logging.getLogger(__name__)


class MeteoKouranCoordinator(DataUpdateCoordinator[Any]):
    """Reads /api/v1/<resource> at the package's pace; data is the decoded JSON."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, resource: str) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"MétéoKouran /{resource}",
            update_interval=SCAN_INTERVALS[resource],
        )
        self.resource = resource
        self._url = entry.data[CONF_URL]
        self._session = async_get_clientsession(hass)

    async def _async_update_data(self) -> Any:
        try:
            return await async_fetch(self._session, self._url, self.resource)
        except MeteoKouranError as err:
            raise UpdateFailed(f"{self._url}/api/v1/{self.resource}: {type(err).__name__} {err}") from err

    @property
    def payload(self) -> Any:
        """Last answer, or None when the last request failed (entities then unavailable)."""
        return self.data if self.last_update_success else None
