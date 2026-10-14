"""Camera platform for the Tridonic FalcoSENSE integration."""

import io
import logging
from typing import override

from falcosense import ShapeGeometry
from PIL import Image, ImageColor, ImageDraw, ImageFont

from homeassistant.components.camera import Camera
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_OVERLAY, DOMAIN
from .coordinator import FalcoSenseConfigEntry, FalcoSenseCoordinator
from .entity import main_identifier

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0

# The device frame is low resolution. Draw the overlay on an upscaled canvas so
# the lines and labels stay crisp instead of inheriting the frame's pixelation.
_UPSCALE = 4
_FALLBACK_COLOR = (255, 255, 255)


def _draw_overlay(frame: bytes, annotations: list[ShapeGeometry]) -> bytes:
    """Draw the commissioned lines and areas onto a frame (runs in executor)."""
    image = Image.open(io.BytesIO(frame)).convert("RGB")
    width, height = (dimension * _UPSCALE for dimension in image.size)
    image = image.resize((width, height), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(image)
    line_width = max(1, min(width, height) // 160)
    font = ImageFont.load_default(size=max(12, height // 28))
    for shape in annotations:
        try:
            color = ImageColor.getrgb(shape.color)
        except ValueError:
            color = _FALLBACK_COLOR
        if shape.is_line:
            if shape.start is not None and shape.end is not None:
                start = (shape.start[0] * width, shape.start[1] * height)
                end = (shape.end[0] * width, shape.end[1] * height)
                draw.line([start, end], fill=color, width=line_width)
                draw.text(start, shape.label, fill=color, font=font)
        elif len(shape.points) >= 2:
            points = [(x * width, y * height) for x, y in shape.points]
            draw.polygon(points, outline=color, width=line_width)
            draw.text(points[0], shape.label, fill=color, font=font)
    output = io.BytesIO()
    image.save(output, format="JPEG")
    return output.getvalue()


async def async_setup_entry(
    hass: HomeAssistant,
    entry: FalcoSenseConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the FalcoSENSE camera from a config entry."""
    async_add_entities([FalcoSenseCamera(entry.runtime_data)])


class FalcoSenseCamera(CoordinatorEntity[FalcoSenseCoordinator], Camera):
    """The sensor's debug camera frame, optionally overlaid with shapes."""

    _attr_has_entity_name = True
    _attr_translation_key = "debug"
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator: FalcoSenseCoordinator) -> None:
        """Initialize the camera."""
        super().__init__(coordinator)
        Camera.__init__(self)
        identifier = main_identifier(coordinator)
        self._attr_unique_id = identifier
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, identifier)})

    @override
    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return the latest camera frame, overlaid with shapes if enabled."""
        frame = self.coordinator.data.camera_frame
        if frame is None:
            return None
        annotations = self.coordinator.data.annotations
        if not annotations or not self.coordinator.config_entry.options.get(
            CONF_OVERLAY, True
        ):
            return frame
        try:
            return await self.hass.async_add_executor_job(
                _draw_overlay, frame, annotations
            )
        except OSError as err:
            # A truncated or corrupt frame must not break the camera; fall back
            # to the raw frame and try again on the next one.
            _LOGGER.debug("Could not render camera overlay: %s", err)
            return frame
