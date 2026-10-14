"""Device registration for the Tridonic FalcoSENSE integration."""

from falcosense import FalcoSenseState

from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .const import DEVICE_PORT, DOMAIN, MANUFACTURER, MODEL
from .coordinator import FalcoSenseConfigEntry


def async_register_devices(
    hass: HomeAssistant,
    entry: FalcoSenseConfigEntry,
    state: FalcoSenseState,
) -> None:
    """Register the main device and one sub-device per commissioned shape."""
    device_registry = dr.async_get(hass)
    serial = entry.unique_id
    assert serial is not None

    main_device = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, serial)},
        manufacturer=MANUFACTURER,
        model=MODEL,
        name=f"{MODEL} {serial}",
        serial_number=serial,
        sw_version=state.device.firmware_version,
        configuration_url=f"https://{entry.data[CONF_HOST]}:{DEVICE_PORT}",
    )

    shapes = (
        *((line.uid, line.label, "Line") for line in state.lines.values()),
        *((area.uid, area.label, "Area") for area in state.areas.values()),
        *((queue.uid, queue.label, "Queue") for queue in state.queues.values()),
    )
    for uid, label, kind in shapes:
        device_registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers={(DOMAIN, f"{serial}_{uid}")},
            manufacturer=MANUFACTURER,
            model=f"{MODEL} {kind}",
            name=f"{serial} {label}",
            via_device_id=main_device.id,
        )
