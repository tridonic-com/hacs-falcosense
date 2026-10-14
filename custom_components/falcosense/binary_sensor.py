"""Binary sensor platform for the Tridonic FalcoSENSE integration."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import override

from falcosense import Area, DeviceInfo, Line

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import FalcoSenseConfigEntry, FalcoSenseCoordinator
from .entity import FalcoSenseEntity, FalcoSenseShapeEntity

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class FalcoSenseLineBinaryDescription(BinarySensorEntityDescription):
    """Describes a line binary sensor."""

    value_fn: Callable[[Line], bool | None]


@dataclass(frozen=True, kw_only=True)
class FalcoSenseAreaBinaryDescription(BinarySensorEntityDescription):
    """Describes an area binary sensor."""

    value_fn: Callable[[Area], bool | None]


@dataclass(frozen=True, kw_only=True)
class FalcoSenseDeviceBinaryDescription(BinarySensorEntityDescription):
    """Describes a device-level binary sensor."""

    value_fn: Callable[[DeviceInfo], bool | None]


LINE_BINARY_SENSORS: tuple[FalcoSenseLineBinaryDescription, ...] = (
    FalcoSenseLineBinaryDescription(
        key="in_alert",
        translation_key="in_alert",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda line: line.in_alert,
    ),
    FalcoSenseLineBinaryDescription(
        key="out_alert",
        translation_key="out_alert",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda line: line.out_alert,
    ),
)

AREA_BINARY_SENSORS: tuple[FalcoSenseAreaBinaryDescription, ...] = (
    FalcoSenseAreaBinaryDescription(
        key="occupancy_alert",
        translation_key="occupancy_alert",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda area: area.occupancy_alert,
    ),
    FalcoSenseAreaBinaryDescription(
        key="dwell_time_alert",
        translation_key="dwell_time_alert",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda area: area.dwell_time_alert,
    ),
    FalcoSenseAreaBinaryDescription(
        key="dwell_avg_time_alert",
        translation_key="dwell_avg_time_alert",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda area: area.dwell_avg_time_alert,
    ),
)

DEVICE_BINARY_SENSORS: tuple[FalcoSenseDeviceBinaryDescription, ...] = (
    FalcoSenseDeviceBinaryDescription(
        key="running",
        device_class=BinarySensorDeviceClass.RUNNING,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda device: device.running,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: FalcoSenseConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up FalcoSENSE binary sensors from a config entry."""
    coordinator = entry.runtime_data

    async_add_entities(
        FalcoSenseDeviceBinarySensor(coordinator, description)
        for description in DEVICE_BINARY_SENSORS
    )

    known: set[str] = set()

    @callback
    def _add_new_shapes() -> None:
        state = coordinator.data
        entities: list[BinarySensorEntity] = []
        for line in state.lines.values():
            if line.uid not in known:
                known.add(line.uid)
                entities.extend(
                    FalcoSenseLineBinarySensor(coordinator, d, line)
                    for d in LINE_BINARY_SENSORS
                )
        for area in state.areas.values():
            if area.uid not in known:
                known.add(area.uid)
                entities.extend(
                    FalcoSenseAreaBinarySensor(coordinator, d, area)
                    for d in AREA_BINARY_SENSORS
                )
        if entities:
            async_add_entities(entities)

    _add_new_shapes()
    entry.async_on_unload(coordinator.async_add_listener(_add_new_shapes))


class FalcoSenseDeviceBinarySensor(FalcoSenseEntity, BinarySensorEntity):
    """A device-level FalcoSENSE binary sensor."""

    entity_description: FalcoSenseDeviceBinaryDescription

    @property
    @override
    def is_on(self) -> bool | None:
        """Return the binary sensor state."""
        return self.entity_description.value_fn(self.coordinator.data.device)


class FalcoSenseLineBinarySensor(FalcoSenseShapeEntity, BinarySensorEntity):
    """An alert binary sensor for a counting line."""

    entity_description: FalcoSenseLineBinaryDescription

    def __init__(
        self,
        coordinator: FalcoSenseCoordinator,
        description: FalcoSenseLineBinaryDescription,
        line: Line,
    ) -> None:
        """Initialize the line binary sensor."""
        super().__init__(coordinator, description, line.uid)

    @property
    @override
    def is_on(self) -> bool | None:
        """Return the binary sensor state."""
        line = self.coordinator.data.lines.get(self._shape_uid)
        if line is None:
            return None
        return self.entity_description.value_fn(line)


class FalcoSenseAreaBinarySensor(FalcoSenseShapeEntity, BinarySensorEntity):
    """An alert binary sensor for a dwell area."""

    entity_description: FalcoSenseAreaBinaryDescription

    def __init__(
        self,
        coordinator: FalcoSenseCoordinator,
        description: FalcoSenseAreaBinaryDescription,
        area: Area,
    ) -> None:
        """Initialize the area binary sensor."""
        super().__init__(coordinator, description, area.uid)

    @property
    @override
    def is_on(self) -> bool | None:
        """Return the binary sensor state."""
        area = self.coordinator.data.areas.get(self._shape_uid)
        if area is None:
            return None
        return self.entity_description.value_fn(area)
