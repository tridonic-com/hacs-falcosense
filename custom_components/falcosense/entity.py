"""Base entities for the Tridonic FalcoSENSE integration."""

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import FalcoSenseCoordinator


def main_identifier(coordinator: FalcoSenseCoordinator) -> str:
    """Return the stable identifier of the main device."""
    assert coordinator.config_entry.unique_id is not None
    return coordinator.config_entry.unique_id


def shape_identifier(coordinator: FalcoSenseCoordinator, shape_uid: str) -> str:
    """Return the stable identifier of a shape sub-device."""
    return f"{main_identifier(coordinator)}_{shape_uid}"


class FalcoSenseEntity(CoordinatorEntity[FalcoSenseCoordinator]):
    """Base entity attached to the main FalcoSENSE device."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: FalcoSenseCoordinator,
        description: EntityDescription,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self.entity_description = description
        identifier = main_identifier(coordinator)
        self._attr_unique_id = f"{identifier}_{description.key}"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, identifier)})


class FalcoSenseShapeEntity(CoordinatorEntity[FalcoSenseCoordinator]):
    """Base entity for a commissioned line, area or queue (a sub-device)."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: FalcoSenseCoordinator,
        description: EntityDescription,
        shape_uid: str,
    ) -> None:
        """Initialize the shape entity."""
        super().__init__(coordinator)
        self.entity_description = description
        self._shape_uid = shape_uid
        self._attr_unique_id = (
            f"{main_identifier(coordinator)}_{shape_uid}_{description.key}"
        )
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, shape_identifier(coordinator, shape_uid))}
        )
