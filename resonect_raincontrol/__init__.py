import logging
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the integration via YAML."""
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the integration via the UI."""
    _LOGGER.info("Setting up My Integration from config entry")

    await hass.config_entries.async_forward_entry_setup(entry, "switch")
    await hass.config_entries.async_forward_entry_setup(entry, "button")
    await hass.config_entries.async_forward_entry_setup(entry, "sensor")

    # Show a notification when demo mode is enabled
    create_demo_mode_alert(hass)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    await hass.config_entries.async_forward_entry_unload(entry, "switch")
    await hass.config_entries.async_forward_entry_unload(entry, "button")
    await hass.config_entries.async_forward_entry_unload(entry, "sensor")

    return True


def create_demo_mode_alert(hass: HomeAssistant):
    """Create a persistent notification in Home Assistant for demo mode."""
    hass.components.persistent_notification.create(
        "Je potřeba vyměnit UV lampu.",
        title="Nutnost výměny UV lampy",
        notification_id="demo_mode_uv",
    )
    hass.components.persistent_notification.create(
        "Je třeba vyměnit filtry.",
        title="Nutnost výměny filtrů",
        notification_id="demo_mode_filter",
    )
