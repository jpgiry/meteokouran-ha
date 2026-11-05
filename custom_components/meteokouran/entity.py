"""Base entity: reads one or more coordinators through a pure function of logic.py."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity import Entity

from .const import DOMAIN, NAME
from .coordinator import MeteoKouranCoordinator
from .logic import Value


@dataclass(frozen=True, kw_only=True)
class MeteoKouranDescription:
    """Mixed into the platform's entity description.

    object_id: fixed, the YAML package's (automations rely on it).
    resources: coordinators read, in the order `compute` takes their answers.
    unavailable_icon: icon kept while unavailable (the package's static or
    template icons stay; its REST signal sensors have none then).
    """

    object_id: str
    resources: tuple[str, ...]
    compute: Callable[..., Value | None]
    unavailable_icon: str | None = None


class MeteoKouranEntity(Entity):
    """An entity of the MétéoKouran device; unavailable when `compute` returns None."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    entity_description: MeteoKouranDescription

    def __init__(
        self,
        coordinators: dict[str, MeteoKouranCoordinator],
        description: MeteoKouranDescription,
        platform_domain: str,
    ) -> None:
        self.entity_description = description
        self._coordinators = [coordinators[r] for r in description.resources]
        # Same entity_id as the YAML package whatever the language of Home
        # Assistant (HA derives ids from translated names otherwise).
        self.entity_id = f"{platform_domain}.{description.object_id}"
        # Same unique_id as the package: one MétéoKouran instance per HA.
        self._attr_unique_id = description.key
        self._attr_translation_key = description.translation_key
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, DOMAIN)},
            name=NAME,
            manufacturer=NAME,
            entry_type=DeviceEntryType.SERVICE,
        )
        self._value: Value | None = None
        self._compute()

    def _compute(self) -> None:
        self._value = self.entity_description.compute(*(c.payload for c in self._coordinators))

    async def async_added_to_hass(self) -> None:
        for coordinator in self._coordinators:
            self.async_on_remove(coordinator.async_add_listener(self._handle_update))

    @callback
    def _handle_update(self) -> None:
        self._compute()
        self.async_write_ha_state()

    @property
    def available(self) -> bool:
        return self._value is not None

    @property
    def icon(self) -> str | None:
        return self._value.icon if self._value else self.entity_description.unavailable_icon

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        return dict(self._value.attributes) if self._value else None
