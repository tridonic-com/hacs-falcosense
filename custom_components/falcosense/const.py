"""Constants for the Tridonic FalcoSENSE integration."""

from homeassistant.const import Platform

DOMAIN = "falcosense"

PLATFORMS = [Platform.BINARY_SENSOR, Platform.CAMERA, Platform.SENSOR]

MANUFACTURER = "Tridonic"
MODEL = "FalcoSENSE"

DEVICE_PORT = 5000

CONF_OVERLAY = "overlay"
