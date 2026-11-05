"""Constants of the MétéoKouran integration."""

from datetime import timedelta
from typing import Final

DOMAIN: Final = "meteokouran"
NAME: Final = "MétéoKouran"

CONF_URL: Final = "url"
# The only default address: the public instance.
DEFAULT_URL: Final = "https://meteokouran.re"

# Same pace as the YAML package: /now and /cyclone every 15 min, /forecast
# every 30 min, 20 s timeout. One request per resource and per cycle, shared
# by every entity reading it.
RESOURCE_NOW: Final = "now"
RESOURCE_FORECAST: Final = "forecast"
RESOURCE_CYCLONE: Final = "cyclone"
SCAN_INTERVALS: Final = {
    RESOURCE_NOW: timedelta(minutes=15),
    RESOURCE_FORECAST: timedelta(minutes=30),
    RESOURCE_CYCLONE: timedelta(minutes=15),
}
TIMEOUT: Final = 20

# Embedded card, served by the integration and loaded by the frontend.
CARD_FILENAME: Final = "meteokouran-card.js"
CARD_URL_PATH: Final = f"/{DOMAIN}/{CARD_FILENAME}"
# Websocket command the card calls for the configured URL.
WS_TYPE_CONFIG: Final = f"{DOMAIN}/config"
