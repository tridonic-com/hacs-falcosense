"""The Tridonic FalcoSENSE integration."""

from falcosense import FalcoSense

from homeassistant.const import CONF_HOST, CONF_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import PLATFORMS
from .coordinator import FalcoSenseConfigEntry, FalcoSenseCoordinator
from .devices import async_register_devices


async def async_setup_entry(hass: HomeAssistant, entry: FalcoSenseConfigEntry) -> bool:
    """Set up Tridonic FalcoSENSE from a config entry."""
    client = FalcoSense(
        entry.data[CONF_HOST],
        entry.data[CONF_TOKEN],
        async_get_clientsession(hass, verify_ssl=False),
    )

    coordinator = FalcoSenseCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    async_register_devices(hass, entry, coordinator.data)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: FalcoSenseConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        await entry.runtime_data.async_shutdown()
    return unload_ok
