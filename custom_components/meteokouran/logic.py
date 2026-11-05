"""State, attributes and icon of every entity, from the API answers (pure functions).

Each function reproduces the YAML package (homeassistant/meteokouran.yaml of the
MétéoKouran repository, 1.x): same states, same attributes, same icons, and
"unavailable, never off" when the API cannot tell. A function returns None
when its entity is unavailable, else a Value.

`now`, `forecast` and `cyclone` are the decoded answers of /api/v1/now,
/api/v1/forecast and /api/v1/cyclone, or None when the last request failed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

SIGNAL_ICONS = {
    "vert": "mdi:transmission-tower",
    "orange": "mdi:transmission-tower-export",
    "rouge": "mdi:transmission-tower-off",
    "bleu": "mdi:clock-alert-outline",
}
DEFAULT_ICON = "mdi:transmission-tower"
CONSTRAINED = ("orange", "rouge", "bleu")


@dataclass(frozen=True)
class Value:
    """State (native value), extra attributes and icon of an available entity."""

    state: Any
    attributes: dict[str, Any] = field(default_factory=dict)
    icon: str | None = None


def _data(payload: Any) -> dict | None:
    """The "data" object of an answer, or None."""
    if isinstance(payload, dict) and isinstance(payload.get("data"), dict):
        return payload["data"]
    return None


def _source(payload: Any) -> dict:
    """The "source" object of an answer (licence: attribution, updated_at), or {}."""
    if isinstance(payload, dict) and isinstance(payload.get("source"), dict):
        return payload["source"]
    return {}


def _licence(payload: Any) -> dict[str, Any]:
    """`attribution` and `source_updated_at` (Etalab 2.0: source and EDF update date)."""
    source = _source(payload)
    return {"attribution": source.get("attribution"), "source_updated_at": source.get("updated_at")}


def _pick(obj: dict, keys: tuple[str, ...]) -> dict[str, Any]:
    """Like the REST json_attributes: the listed keys present in obj."""
    return {key: obj[key] for key in keys if key in obj}


def _signal_key(obj: Any) -> str | None:
    signal = obj.get("signal") if isinstance(obj, dict) else None
    return signal.get("key") if isinstance(signal, dict) else None


def _signal_value(obj: dict, attributes: dict[str, Any]) -> Value | None:
    key = _signal_key(obj)
    if key is None:
        return None
    return Value(key, attributes, SIGNAL_ICONS.get(key, DEFAULT_ICON))


# ---------------------------------------------------------------- /now ----


def signal_horaire(now: Any) -> Value | None:
    """sensor.meteokouran_signal_horaire: signal of the current hour."""
    data = _data(now)
    if data is None or not isinstance(data.get("hour"), dict):
        return None
    return _signal_value(data["hour"], _pick(now, ("data", "meta", "source")))


def signal_du_jour(now: Any) -> Value | None:
    """sensor.meteokouran_signal_du_jour: signal of the day."""
    data = _data(now)
    day = data.get("day") if data else None
    if not isinstance(day, dict):
        return None
    # Unavailable while the day is not published (signal null): no key.
    return _signal_value(day, _pick(day, ("date", "signal")))


def prochain_changement(now: Any) -> Value | None:
    """sensor.meteokouran_prochain_changement: time of the next signal change.

    Unknown (state None) when no change is expected until the end of J+4.
    """
    if signal_horaire(now) is None:
        return None
    nxt = _data(now).get("next_change")
    signal = nxt.get("signal") if isinstance(nxt, dict) else None
    signal = signal if isinstance(signal, dict) else {}
    at = nxt.get("at") if isinstance(nxt, dict) else None
    return Value(
        datetime.fromisoformat(at) if isinstance(at, str) else None,
        {"key": signal.get("key") if nxt else None, "label": signal.get("label") if nxt else None, **_licence(now)},
        "mdi:clock-start",
    )


def reseau_contraint(now: Any) -> Value | None:
    """binary_sensor.meteokouran_reseau_contraint: on for orange, rouge and bleu."""
    horaire = signal_horaire(now)
    if horaire is None:
        return None
    on = horaire.state in CONSTRAINED
    hour = _data(now).get("hour")
    return Value(
        on,
        {"key": horaire.state, "label": hour["signal"].get("label"), **_licence(now)},
        "mdi:transmission-tower-off" if on else "mdi:transmission-tower",
    )


# ----------------------------------------------------------- /forecast ----


def _tomorrow(forecast: Any) -> dict | None:
    data = _data(forecast)
    days = data.get("days") if data else None
    if not isinstance(days, list) or len(days) < 2 or not isinstance(days[1], dict):
        return None
    return days[1]


def signal_de_demain(forecast: Any) -> Value | None:
    """sensor.meteokouran_signal_de_demain: signal of J+1 (unavailable until EDF publishes it)."""
    day = _tomorrow(forecast)
    if day is None or day.get("signal") is None:
        return None
    return _signal_value(day, _pick(day, ("date", "signal", "hours")))


def ranges_text(hours: list[dict]) -> str:
    """Non-green hours grouped in ranges: "18:00–22:00 Heures de pointe" ; "Aucune".

    A range ends at the end of its last hour; a missing hour splits it.
    """
    out: list[str] = []
    key, label, start, end = "vert", "", "", -1
    for h in [*[h for h in hours if h.get("signal")], None]:
        h_key = h["signal"]["key"] if h else "end"
        hour = int(h["start"][11:13]) if h else -2
        if h_key != key or hour != end:
            if key not in ("vert", "end"):
                out.append(f"{start}–{('0' + str(end))[-2:]}:00 {label}")
            key = h_key
            label = h["signal"]["label"] if h else ""
            start = h["start"][11:16] if h else ""
        end = hour + 1
    return (" ; ".join(out) or "Aucune")[:255]


def pointes_de_demain(forecast: Any, now: Any) -> Value | None:
    """sensor.meteokouran_pointes_de_demain: tomorrow's non-green ranges.

    Licence attributes come from /now, as in the package.
    """
    demain = signal_de_demain(forecast)
    if demain is None:
        return None
    hours = demain.attributes.get("hours") or []
    return Value(ranges_text(hours), _licence(signal_horaire(now) and now), "mdi:clock-alert-outline")


# ------------------------------------------------------------ /cyclone ----


def donnees_cyclone(cyclone: Any) -> Value | None:
    """sensor.meteokouran_donnees_cyclone: oui / non / inconnu, with the raw answer."""
    data = _data(cyclone)
    if data is None or "en_cours" not in data:
        return None
    en_cours = data["en_cours"]
    state = "inconnu" if en_cours is None else ("oui" if en_cours else "non")
    return Value(state, _pick(cyclone, ("data", "meta", "source")), "mdi:weather-hurricane-outline")


def plages_text(hours: list[str]) -> str | None:
    """Flagged hours as ranges: "13/10 14:00 → 14/10 06:00" (end of the last hour), None when none."""
    out: list[str] = []
    start = prev = None
    for h in [*hours, None]:
        if h is None or prev is None or datetime.fromisoformat(h).timestamp() - datetime.fromisoformat(prev).timestamp() != 3600:
            if start is not None:
                end = ("0" + str(int(prev[11:13]) + 1))[-2:]
                out.append(f"{start[8:10]}/{start[5:7]} {start[11:16]} → {prev[8:10]}/{prev[5:7]} {end}:00")
            start = h
        prev = h
    return " ; ".join(out) if out else None


def cyclone_en_cours(cyclone: Any) -> Value | None:
    """binary_sensor.meteokouran_cyclone_en_cours: EDF's flag for the current hour."""
    if donnees_cyclone(cyclone) is None:
        return None
    data = _data(cyclone)
    if data["en_cours"] is None:
        return None
    hours = data.get("heures_publiees_a_true") or []
    return Value(
        bool(data["en_cours"]),
        {
            "depuis": data.get("depuis"),
            "heures_publiees_a_true": hours,
            "plage_publiee": plages_text(hours),
            "dernier_episode": data.get("dernier_episode"),
            **_licence(cyclone),
        },
        "mdi:weather-hurricane" if data["en_cours"] else "mdi:weather-hurricane-outline",
    )


def cyclone_annonce(cyclone: Any) -> Value | None:
    """binary_sensor.meteokouran_cyclone_annonce: an hour flagged from now to the end of J+4."""
    if donnees_cyclone(cyclone) is None:
        return None
    data = _data(cyclone)
    if data.get("annonce") is None:
        return None
    return Value(
        bool(data["annonce"]),
        {"premiere_heure_annoncee": data.get("premiere_heure_annoncee"), **_licence(cyclone)},
        "mdi:weather-hurricane" if data["annonce"] else "mdi:weather-hurricane-outline",
    )
