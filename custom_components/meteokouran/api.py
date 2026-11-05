"""Access to the public MétéoKouran API (no dependency: Home Assistant's aiohttp session)."""

from __future__ import annotations

import asyncio
import re
from typing import Any
from urllib.parse import urlsplit

import aiohttp

from .const import TIMEOUT


class MeteoKouranError(Exception):
    """Base error of the API client."""


class CannotConnect(MeteoKouranError):
    """The instance cannot be reached (network error or server error)."""


class Timeout(MeteoKouranError):
    """No answer within the timeout."""


class NotMeteoKouran(MeteoKouranError):
    """Something answered, but not a MétéoKouran instance."""


class InvalidUrl(MeteoKouranError):
    """Not an http(s) address."""


_API_SUFFIX = re.compile(r"(/api(/v1)?)?/*$", re.IGNORECASE)


def normalize_url(text: str) -> str:
    """Base URL of an instance: spaces, trailing "/" and a pasted "/api/v1" removed.

    Raises InvalidUrl when the result is not an http(s) URL with a host.
    """
    url = _API_SUFFIX.sub("", (text or "").strip())
    parts = urlsplit(url)
    if parts.scheme.lower() not in ("http", "https") or not parts.hostname or parts.query or parts.fragment:
        raise InvalidUrl(text)
    if any(c.isspace() for c in url):
        raise InvalidUrl(text)
    return f"{parts.scheme.lower()}://{parts.netloc.lower()}{parts.path}"


async def async_fetch(session: aiohttp.ClientSession, base_url: str, resource: str) -> Any:
    """GET {base_url}/api/v1/{resource}, decoded JSON (any JSON value).

    Raises Timeout, CannotConnect (network error, 5xx, 429) or NotMeteoKouran
    (other HTTP status, or a body that is not JSON).
    """
    try:
        async with asyncio.timeout(TIMEOUT):
            async with session.get(
                f"{base_url}/api/v1/{resource}", headers={"Accept": "application/json"}
            ) as response:
                if response.status >= 500 or response.status == 429:
                    raise CannotConnect(f"HTTP {response.status}")
                if response.status != 200:
                    raise NotMeteoKouran(f"HTTP {response.status}")
                try:
                    return await response.json(content_type=None)
                except ValueError as err:
                    raise NotMeteoKouran("not JSON") from err
    except TimeoutError as err:
        raise Timeout from err
    except aiohttp.ClientError as err:
        raise CannotConnect(str(err)) from err


def looks_like_now(payload: Any) -> bool:
    """True when `payload` has the shape of /api/v1/now (data.hour, data.day, source)."""
    if not isinstance(payload, dict):
        return False
    data = payload.get("data")
    return (
        isinstance(data, dict)
        and "hour" in data
        and "day" in data
        and isinstance(payload.get("source"), dict)
    )


async def async_validate(session: aiohttp.ClientSession, base_url: str) -> None:
    """Check that base_url is a MétéoKouran instance, by reading /api/v1/now."""
    if not looks_like_now(await async_fetch(session, base_url, "now")):
        raise NotMeteoKouran("unexpected answer")
