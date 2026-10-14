"""The Tridonic FalcoSENSE integration."""

from falcosense import FalcoSense

from homeassistant.const import CONF_HOST, CONF_TOKEN, Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, PLATFORMS
from .coordinator import FalcoSenseConfigEntry, FalcoSenseCoordinator
from .devices import async_register_devices


@callback
def _async_migrate_camera_unique_id(
    hass: HomeAssistant, entry: FalcoSenseConfigEntry
) -> None:
    """Migrate the legacy ``<serial>_camera`` camera unique ID to ``<serial>``.

    Early builds registered the camera with the platform name in its unique ID.
    Rename the registry entry so upgrades do not create a duplicate camera.
    """
    entity_registry = er.async_get(hass)
    serial = entry.unique_id
    assert serial is not None
    old_entity_id = entity_registry.async_get_entity_id(
        Platform.CAMERA, DOMAIN, f"{serial}_camera"
    )
    if old_entity_id is None or entity_registry.async_get_entity_id(
        Platform.CAMERA, DOMAIN, serial
    ):
        return
    entity_registry.async_update_entity(old_entity_id, new_unique_id=serial)


async def async_setup_entry(hass: HomeAssistant, entry: FalcoSenseConfigEntry) -> bool:
    """Set up Tridonic FalcoSENSE from a config entry."""
    _async_migrate_camera_unique_id(hass, entry)

    client = FalcoSense(
        entry.data[CONF_HOST],
        entry.data[CONF_TOKEN],
        async_get_clientsession(hass, verify_ssl=False),
    )

    coordinator = FalcoSenseCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    # Register the main device and the currently commissioned shapes, and keep
    # registering shapes that appear later (dynamic devices).
    known_shapes: set[str] = set()

    @callback
    def _register_devices() -> None:
        state = coordinator.data
        shapes = set(state.lines) | set(state.areas) | set(state.queues)
        if shapes == known_shapes:
            return
        known_shapes.clear()
        known_shapes.update(shapes)
        async_register_devices(hass, entry, state)

    _register_devices()
    entry.async_on_unload(coordinator.async_add_listener(_register_devices))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_remove_config_entry_device(
    hass: HomeAssistant,
    entry: FalcoSenseConfigEntry,
    device_entry: dr.AnyDeviceEntry,
) -> bool:
    """Allow removing a device whose shape is no longer commissioned."""
    state = entry.runtime_data.data
    serial = entry.unique_id
    current = {
        serial,
        *(f"{serial}_{uid}" for uid in (*state.lines, *state.areas, *state.queues)),
    }
    return not any(
        identifier[1] in current
        for identifier in device_entry.identifiers
        if identifier[0] == DOMAIN
    )


async def async_unload_entry(hass: HomeAssistant, entry: FalcoSenseConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        await entry.runtime_data.async_shutdown()
    return unload_ok
