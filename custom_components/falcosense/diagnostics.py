"""Diagnostics support for the Tridonic FalcoSENSE integration."""

from dataclasses import asdict
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_HOST, CONF_TOKEN
from homeassistant.core import HomeAssistant

from .coordinator import FalcoSenseConfigEntry

TO_REDACT = {CONF_TOKEN, CONF_HOST}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: FalcoSenseConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    state = entry.runtime_data.data
    return {
        "entry_data": async_redact_data(entry.data, TO_REDACT),
        "device": asdict(state.device),
        "lines": [asdict(line) for line in state.lines.values()],
        "areas": [asdict(area) for area in state.areas.values()],
        "queues": [asdict(queue) for queue in state.queues.values()],
    }
