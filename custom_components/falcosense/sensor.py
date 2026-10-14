"""Sensor platform for the Tridonic FalcoSENSE integration."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import override

from falcosense import Area, DeviceInfo, Line, Queue

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import EntityCategory, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import StateType

from .coordinator import FalcoSenseConfigEntry, FalcoSenseCoordinator
from .entity import FalcoSenseEntity, FalcoSenseShapeEntity

PARALLEL_UPDATES = 0

UNIT_PEOPLE = "people"


@dataclass(frozen=True, kw_only=True)
class FalcoSenseLineSensorDescription(SensorEntityDescription):
    """Describes a line sensor."""

    value_fn: Callable[[Line], StateType]


@dataclass(frozen=True, kw_only=True)
class FalcoSenseAreaSensorDescription(SensorEntityDescription):
    """Describes an area sensor."""

    value_fn: Callable[[Area], StateType]


@dataclass(frozen=True, kw_only=True)
class FalcoSenseQueueSensorDescription(SensorEntityDescription):
    """Describes a queue sensor."""

    value_fn: Callable[[Queue], StateType]


@dataclass(frozen=True, kw_only=True)
class FalcoSenseDeviceSensorDescription(SensorEntityDescription):
    """Describes a device-level sensor."""

    value_fn: Callable[[DeviceInfo], StateType]


LINE_SENSORS: tuple[FalcoSenseLineSensorDescription, ...] = (
    FalcoSenseLineSensorDescription(
        key="people_in",
        translation_key="people_in",
        native_unit_of_measurement=UNIT_PEOPLE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda line: line.people_in,
    ),
    FalcoSenseLineSensorDescription(
        key="people_out",
        translation_key="people_out",
        native_unit_of_measurement=UNIT_PEOPLE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda line: line.people_out,
    ),
)

AREA_SENSORS: tuple[FalcoSenseAreaSensorDescription, ...] = (
    FalcoSenseAreaSensorDescription(
        key="occupancy",
        translation_key="occupancy",
        native_unit_of_measurement=UNIT_PEOPLE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda area: area.occupancy,
    ),
    FalcoSenseAreaSensorDescription(
        key="people_per_minute",
        translation_key="people_per_minute",
        native_unit_of_measurement=UNIT_PEOPLE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda area: area.people_per_minute,
    ),
    FalcoSenseAreaSensorDescription(
        key="minutes_occupied",
        translation_key="minutes_occupied",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda area: area.minutes_occupied,
    ),
    FalcoSenseAreaSensorDescription(
        key="mean_dwell_time",
        translation_key="mean_dwell_time",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda area: area.mean_dwell_time,
    ),
)

QUEUE_SENSORS: tuple[FalcoSenseQueueSensorDescription, ...] = (
    FalcoSenseQueueSensorDescription(
        key="queue_occupancy",
        translation_key="queue_occupancy",
        native_unit_of_measurement=UNIT_PEOPLE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda queue: queue.occupancy,
    ),
    FalcoSenseQueueSensorDescription(
        key="queue_average_waiting_time",
        translation_key="queue_average_waiting_time",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda queue: queue.average_waiting_time,
    ),
    FalcoSenseQueueSensorDescription(
        key="queue_people_per_minute",
        translation_key="queue_people_per_minute",
        native_unit_of_measurement=UNIT_PEOPLE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda queue: queue.people_per_minute,
    ),
    FalcoSenseQueueSensorDescription(
        key="mean_queue_time",
        translation_key="mean_queue_time",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda queue: queue.mean_queue_time,
    ),
)

DEVICE_SENSORS: tuple[FalcoSenseDeviceSensorDescription, ...] = (
    FalcoSenseDeviceSensorDescription(
        key="uptime",
        translation_key="uptime",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda device: device.uptime,
    ),
    FalcoSenseDeviceSensorDescription(
        key="timezone",
        translation_key="timezone",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda device: device.timezone,
    ),
    FalcoSenseDeviceSensorDescription(
        key="reset_time",
        translation_key="reset_time",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda device: device.reset_time,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: FalcoSenseConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up FalcoSENSE sensors from a config entry."""
    coordinator = entry.runtime_data
    state = coordinator.data

    entities: list[SensorEntity] = [
        FalcoSenseDeviceSensor(coordinator, description)
        for description in DEVICE_SENSORS
    ]
    for line in state.lines.values():
        entities.extend(
            FalcoSenseLineSensor(coordinator, description, line)
            for description in LINE_SENSORS
        )
    for area in state.areas.values():
        entities.extend(
            FalcoSenseAreaSensor(coordinator, description, area)
            for description in AREA_SENSORS
        )
    for queue in state.queues.values():
        entities.extend(
            FalcoSenseQueueSensor(coordinator, description, queue)
            for description in QUEUE_SENSORS
        )

    async_add_entities(entities)


class FalcoSenseDeviceSensor(FalcoSenseEntity, SensorEntity):
    """A device-level FalcoSENSE sensor."""

    entity_description: FalcoSenseDeviceSensorDescription

    @property
    @override
    def native_value(self) -> StateType:
        """Return the sensor value."""
        return self.entity_description.value_fn(self.coordinator.data.device)


class FalcoSenseLineSensor(FalcoSenseShapeEntity, SensorEntity):
    """A sensor for a counting line."""

    entity_description: FalcoSenseLineSensorDescription

    def __init__(
        self,
        coordinator: FalcoSenseCoordinator,
        description: FalcoSenseLineSensorDescription,
        line: Line,
    ) -> None:
        """Initialize the line sensor."""
        super().__init__(coordinator, description, line.uid)

    @property
    @override
    def native_value(self) -> StateType:
        """Return the sensor value."""
        line = self.coordinator.data.lines.get(self._shape_uid)
        if line is None:
            return None
        return self.entity_description.value_fn(line)


class FalcoSenseAreaSensor(FalcoSenseShapeEntity, SensorEntity):
    """A sensor for a dwell area."""

    entity_description: FalcoSenseAreaSensorDescription

    def __init__(
        self,
        coordinator: FalcoSenseCoordinator,
        description: FalcoSenseAreaSensorDescription,
        area: Area,
    ) -> None:
        """Initialize the area sensor."""
        super().__init__(coordinator, description, area.uid)

    @property
    @override
    def native_value(self) -> StateType:
        """Return the sensor value."""
        area = self.coordinator.data.areas.get(self._shape_uid)
        if area is None:
            return None
        return self.entity_description.value_fn(area)


class FalcoSenseQueueSensor(FalcoSenseShapeEntity, SensorEntity):
    """A sensor for a queue."""

    entity_description: FalcoSenseQueueSensorDescription

    def __init__(
        self,
        coordinator: FalcoSenseCoordinator,
        description: FalcoSenseQueueSensorDescription,
        queue: Queue,
    ) -> None:
        """Initialize the queue sensor."""
        super().__init__(coordinator, description, queue.uid)

    @property
    @override
    def native_value(self) -> StateType:
        """Return the sensor value."""
        queue = self.coordinator.data.queues.get(self._shape_uid)
        if queue is None:
            return None
        return self.entity_description.value_fn(queue)
