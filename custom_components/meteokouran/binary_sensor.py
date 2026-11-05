"""MétéoKouran binary sensors: unavailable, never "off", when the API cannot tell."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    DOMAIN as BINARY_SENSOR_DOMAIN,
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import MeteoKouranConfigEntry
from . import logic
from .const import RESOURCE_CYCLONE, RESOURCE_NOW
from .entity import MeteoKouranDescription, MeteoKouranEntity


@dataclass(frozen=True, kw_only=True)
class MeteoKouranBinarySensorDescription(BinarySensorEntityDescription, MeteoKouranDescription):
    """Entity description of a MétéoKouran binary sensor."""


BINARY_SENSORS = (
    MeteoKouranBinarySensorDescription(
        key="meteokouran_reseau_contraint",
        object_id="meteokouran_reseau_contraint",
        translation_key="reseau_contraint",
        resources=(RESOURCE_NOW,),
        compute=logic.reseau_contraint,
        unavailable_icon="mdi:transmission-tower",
    ),
    # Device class as in the package (occupancy: "Détecté" / "Non détecté").
    MeteoKouranBinarySensorDescription(
        key="meteokouran_cyclone_en_cours",
        object_id="meteokouran_cyclone_en_cours",
        translation_key="cyclone_en_cours",
        device_class=BinarySensorDeviceClass.OCCUPANCY,
        resources=(RESOURCE_CYCLONE,),
        compute=logic.cyclone_en_cours,
        unavailable_icon="mdi:weather-hurricane-outline",
    ),
    MeteoKouranBinarySensorDescription(
        key="meteokouran_cyclone_annonce",
        object_id="meteokouran_cyclone_annonce",
        translation_key="cyclone_annonce",
        device_class=BinarySensorDeviceClass.OCCUPANCY,
        resources=(RESOURCE_CYCLONE,),
        compute=logic.cyclone_annonce,
        unavailable_icon="mdi:weather-hurricane-outline",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MeteoKouranConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities(
        MeteoKouranBinarySensor(entry.runtime_data, description, BINARY_SENSOR_DOMAIN)
        for description in BINARY_SENSORS
    )


class MeteoKouranBinarySensor(MeteoKouranEntity, BinarySensorEntity):
    """A MétéoKouran binary sensor."""

    @property
    def is_on(self) -> bool | None:
        return self._value.state if self._value else None
