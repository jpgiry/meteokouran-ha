"""The embedded card: served by the integration, loaded by the frontend, told the URL.

- The file is served at /meteokouran/meteokouran-card.js (static path).
- It is loaded with frontend.add_extra_js_url, whose docstring reads "This
  function allows custom integrations to register extra js or module": the
  frontend loads it on every page, in storage and in YAML dashboard mode alike,
  and nothing is written to the user's dashboard resources (so no duplicate
  resource, nothing left behind after removal). The version in the URL
  (?v=<integration version>) defeats browser and mobile app caches.
- The card asks the configured URL with the websocket command meteokouran/config.
- A dashboard resource still pointing at the former stand-alone card
  (meteokouran-card from HACS or the Marketplace) raises a repair issue: whichever of the two
  files loads first defines the card.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import probatio

from homeassistant.components import websocket_api
from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.components.lovelace.const import LOVELACE_DATA
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import issue_registry as ir
from homeassistant.loader import async_get_integration

from .const import CARD_FILENAME, CARD_URL_PATH, CONF_URL, DOMAIN, WS_TYPE_CONFIG

_LOGGER = logging.getLogger(__name__)
CARD_PATH = Path(__file__).parent / "www" / CARD_FILENAME
ISSUE_OLD_CARD = "old_card_resource"


async def async_setup_frontend(hass: HomeAssistant) -> None:
    """Serve and load the card, register the websocket command, check old resources."""
    websocket_api.async_register_command(hass, ws_config)
    if not await hass.async_add_executor_job(CARD_PATH.is_file):
        _LOGGER.error("Card file missing: %s (reinstall the integration)", CARD_PATH)
        return
    version = (await async_get_integration(hass, DOMAIN)).version
    await hass.http.async_register_static_paths(
        [StaticPathConfig(CARD_URL_PATH, str(CARD_PATH), cache_headers=True)]
    )
    add_extra_js_url(hass, f"{CARD_URL_PATH}?v={version}")
    await async_check_old_resources(hass)


def old_card_resources(items: list[dict[str, Any]]) -> list[str]:
    """URLs of dashboard resources loading another copy of the card."""
    return [
        item["url"]
        for item in items
        if CARD_FILENAME in str(item.get("url", "")) and not str(item["url"]).startswith(CARD_URL_PATH)
    ]


async def async_check_old_resources(hass: HomeAssistant) -> None:
    """Repair issue while a dashboard resource still loads the former stand-alone card."""
    lovelace = hass.data.get(LOVELACE_DATA)
    if lovelace is None:
        return
    await lovelace.resources.async_get_info()  # loads the storage collection
    old = old_card_resources(lovelace.resources.async_items() or [])
    if old:
        ir.async_create_issue(
            hass,
            DOMAIN,
            ISSUE_OLD_CARD,
            is_fixable=False,
            severity=ir.IssueSeverity.WARNING,
            translation_key=ISSUE_OLD_CARD,
            translation_placeholders={"url": ", ".join(old)},
        )
    else:
        ir.async_delete_issue(hass, DOMAIN, ISSUE_OLD_CARD)


@websocket_api.websocket_command({probatio.Required("type"): WS_TYPE_CONFIG})
@callback
def ws_config(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """{"url": base URL of the configured instance, or null when there is none}."""
    entries = hass.config_entries.async_entries(DOMAIN)
    connection.send_result(msg["id"], {"url": entries[0].data[CONF_URL] if entries else None})
