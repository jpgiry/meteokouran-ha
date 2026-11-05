"""Configuration page: the address of the MétéoKouran instance (prefilled with the public one)."""

from __future__ import annotations

from typing import Any

import probatio

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import TextSelector, TextSelectorConfig, TextSelectorType

from .api import CannotConnect, InvalidUrl, NotMeteoKouran, Timeout, async_validate, normalize_url
from .const import CONF_URL, DEFAULT_URL, DOMAIN, NAME

URL_SELECTOR = TextSelector(TextSelectorConfig(type=TextSelectorType.URL))


class MeteoKouranConfigFlow(ConfigFlow, domain=DOMAIN):
    """Add MétéoKouran, or change its address later (reconfigure) without removing it."""

    VERSION = 1

    async def _async_check(self, user_input: dict[str, Any]) -> tuple[str | None, dict[str, str]]:
        """Normalized URL, or the error to show on the URL field."""
        try:
            url = normalize_url(user_input[CONF_URL])
            await async_validate(async_get_clientsession(self.hass), url)
        except InvalidUrl:
            return None, {CONF_URL: "invalid_url"}
        except Timeout:
            return None, {CONF_URL: "timeout"}
        except CannotConnect:
            return None, {CONF_URL: "cannot_connect"}
        except NotMeteoKouran:
            return None, {CONF_URL: "not_meteokouran"}
        return url, {}

    def _form(self, step_id: str, url: str, errors: dict[str, str]) -> ConfigFlowResult:
        return self.async_show_form(
            step_id=step_id,
            data_schema=probatio.Schema({probatio.Required(CONF_URL, default=url): URL_SELECTOR}),
            errors=errors,
            description_placeholders={"default_url": DEFAULT_URL},
        )

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        # One MétéoKouran per Home Assistant: "single_config_entry" in the
        # manifest makes HA refuse a second entry before this step.
        await self.async_set_unique_id(DOMAIN)
        if user_input is None:
            return self._form("user", DEFAULT_URL, {})
        url, errors = await self._async_check(user_input)
        if errors:
            return self._form("user", user_input[CONF_URL], errors)
        return self.async_create_entry(title=NAME, data={CONF_URL: url})

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """New address: saved, then the entry reloads and the API is read again at once."""
        entry = self._get_reconfigure_entry()
        if user_input is None:
            return self._form("reconfigure", entry.data[CONF_URL], {})
        url, errors = await self._async_check(user_input)
        if errors:
            return self._form("reconfigure", user_input[CONF_URL], errors)
        return self.async_update_reload_and_abort(entry, data_updates={CONF_URL: url})
