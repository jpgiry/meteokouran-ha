"""MétéoKouran sensors."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import (
    DOMAIN as SENSOR_DOMAIN,
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import MeteoKouranConfigEntry
from . import logic
from .const import RESOURCE_CYCLONE, RESOURCE_FORECAST, RESOURCE_NOW
from .entity import MeteoKouranDescription, MeteoKouranEntity


@dataclass(frozen=True, kw_only=True)
class MeteoKouranSensorDescription(SensorEntityDescription, MeteoKouranDescription):
    """Entity description of a MétéoKouran sensor."""


SENSORS = (
    MeteoKouranSensorDescription(
        key="meteokouran_signal_horaire",
        object_id="meteokouran_signal_horaire",
        translation_key="signal_horaire",
        resources=(RESOURCE_NOW,),
        compute=logic.signal_horaire,
    ),
    MeteoKouranSensorDescription(
        key="meteokouran_signal_du_jour",
        object_id="meteokouran_signal_du_jour",
        translation_key="signal_du_jour",
        resources=(RESOURCE_NOW,),
        compute=logic.signal_du_jour,
    ),
    MeteoKouranSensorDescription(
        key="meteokouran_signal_demain",
        object_id="meteokouran_signal_de_demain",
        translation_key="signal_de_demain",
        resources=(RESOURCE_FORECAST,),
        compute=logic.signal_de_demain,
    ),
    MeteoKouranSensorDescription(
        key="meteokouran_donnees_cyclone",
        object_id="meteokouran_donnees_cyclone",
        translation_key="donnees_cyclone",
        resources=(RESOURCE_CYCLONE,),
        compute=logic.donnees_cyclone,
        unavailable_icon="mdi:weather-hurricane-outline",
    ),
    MeteoKouranSensorDescription(
        key="meteokouran_prochain_changement",
        object_id="meteokouran_prochain_changement",
        translation_key="prochain_changement",
        device_class=SensorDeviceClass.TIMESTAMP,
        resources=(RESOURCE_NOW,),
        compute=logic.prochain_changement,
        unavailable_icon="mdi:clock-start",
    ),
    MeteoKouranSensorDescription(
        key="meteokouran_pointes_demain",
        object_id="meteokouran_pointes_de_demain",
        translation_key="pointes_de_demain",
        resources=(RESOURCE_FORECAST, RESOURCE_NOW),
        compute=logic.pointes_de_demain,
        unavailable_icon="mdi:clock-alert-outline",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MeteoKouranConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities(
        MeteoKouranSensor(entry.runtime_data, description, SENSOR_DOMAIN) for description in SENSORS
    )


class MeteoKouranSensor(MeteoKouranEntity, SensorEntity):
    """A MétéoKouran sensor."""

    @property
    def native_value(self):
        return self._value.state if self._value else None
