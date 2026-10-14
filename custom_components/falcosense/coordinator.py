"""Coordinator for the Tridonic FalcoSENSE integration."""

import asyncio
import logging
from typing import override

from falcosense import (
    FalcoSense,
    FalcoSenseAuthError,
    FalcoSenseConnectionError,
    FalcoSenseState,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

type FalcoSenseConfigEntry = ConfigEntry[FalcoSenseCoordinator]

FIRST_DATA_TIMEOUT = 30.0


class FalcoSenseCoordinator(DataUpdateCoordinator[FalcoSenseState]):
    """Push coordinator fed by the device's MQTT broker."""

    config_entry: FalcoSenseConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: FalcoSenseConfigEntry,
        client: FalcoSense,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
        )
        self.client = client

    @override
    async def _async_setup(self) -> None:
        """Connect to the device and wait for the first metadata snapshot.

        Only the ``all_metadata`` message carries the commissioned lines, areas
        and queues, so we wait for it before the platforms enumerate shapes.
        """
        self.client.add_listener(self._handle_push)
        self.client.add_connection_listener(self._handle_connection)
        try:
            await self.client.async_validate()
            await self.client.async_connect()
        except FalcoSenseAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except FalcoSenseConnectionError as err:
            raise UpdateFailed(str(err)) from err
        try:
            async with asyncio.timeout(FIRST_DATA_TIMEOUT):
                await self.client.async_wait_for_metadata()
        except TimeoutError as err:
            raise UpdateFailed(
                "Timed out waiting for data from the FalcoSENSE device"
            ) from err

    @override
    async def _async_update_data(self) -> FalcoSenseState:
        """Return the latest accumulated device state."""
        return self.client.state

    @callback
    def _handle_push(self) -> None:
        """Handle a state update pushed over MQTT."""
        self.async_set_updated_data(self.client.state)

    @callback
    def _handle_connection(self, connected: bool) -> None:
        """Mark entities unavailable while the MQTT connection is down.

        Recovery is handled by the next pushed update, which restores
        availability via :meth:`async_set_updated_data`.
        """
        if connected:
            if not self.last_update_success:
                _LOGGER.info("Reconnected to the FalcoSENSE device")
        elif self.last_update_success:
            self.async_set_update_error(
                UpdateFailed("Disconnected from the FalcoSENSE device")
            )

    @override
    async def async_shutdown(self) -> None:
        """Disconnect from the device."""
        await super().async_shutdown()
        await self.client.async_disconnect()
