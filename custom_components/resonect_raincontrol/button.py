import logging
import asyncio
from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    """Set up the button platform."""
    valve_switch = hass.data[DOMAIN].get("valve_switch")

    # If valve_switch is not already set, handle it accordingly
    if valve_switch is None:
        _LOGGER.error("Valve switch not found in Home Assistant data.")
        return

    # Create the ValveCleanButton entity
    valve_clean_button = ValveCleanButton(hass, "Valve Clean Button", valve_switch)

    # Add the button entity to Home Assistant
    async_add_entities([valve_clean_button], update_before_add=True)


class ValveCleanButton(ButtonEntity):
    """Representation of a button to clean the valve."""

    def __init__(self, hass: HomeAssistant, name: str, valve_switch):
        self.hass = hass
        self._name = name
        self._valve_switch = valve_switch  # Reference to the valve switch

    @property
    def name(self):
        """Return the name of the button."""
        return self._name

    async def async_press(self) -> None:
        """Handle the button press."""
        _LOGGER.info("Valve cleaning initiated.")
        await self._clean_valve()

    async def _clean_valve(self):
        """Turn the valve on and off after 5 seconds."""
        _LOGGER.info("Cleaning: Turning valve on.")
        await self._valve_switch.async_turn_on()
        await asyncio.sleep(5)
        _LOGGER.info("Cleaning: Turning valve off.")
        await self._valve_switch.async_turn_off()
        _LOGGER.info("Valve cleaning completed.")
