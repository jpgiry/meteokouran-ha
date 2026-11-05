"""MétéoKouran: EDF Réunion's "météo de l'électricité" from a MétéoKouran instance.

Entities (same entity ids, states and attributes as the former YAML package)
and the dashboard card, in one integration configured from the UI.
"""

from __future__ import annotations

import asyncio

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, RESOURCE_CYCLONE, RESOURCE_FORECAST, RESOURCE_NOW
from .coordinator import MeteoKouranCoordinator
from .frontend import async_setup_frontend

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR]
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

type MeteoKouranConfigEntry = ConfigEntry[dict[str, MeteoKouranCoordinator]]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Once per Home Assistant start: the card and its websocket command."""
    await async_setup_frontend(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: MeteoKouranConfigEntry) -> bool:
    """Read the three resources, then create the entities.

    A failed first read does not stop the setup (no retry loop): the entities
    are created unavailable and the next cycle reads again, as the package did.
    """
    coordinators = {
        resource: MeteoKouranCoordinator(hass, entry, resource)
        for resource in (RESOURCE_NOW, RESOURCE_FORECAST, RESOURCE_CYCLONE)
    }
    await asyncio.gather(*(c.async_refresh() for c in coordinators.values()))
    entry.runtime_data = coordinators
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: MeteoKouranConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
