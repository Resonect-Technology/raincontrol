import asyncio
import json
import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.components import mqtt
from homeassistant.helpers.event import async_track_time_interval, async_call_later

from .button import ValveCleanButton

from datetime import timedelta

from .const import DOMAIN, TOPIC

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    """Set up the switch platform."""
    switch = ValveSwitch(hass, "Valve Switch", "api/v1/valve")
    demo_switch = DemoSwitch(hass, "Demo Mode", "api/v1/demo", switch)

    hass.data[DOMAIN]["valve_switch"] = switch

    async_add_entities([switch, demo_switch], update_before_add=True)


class ValveSwitch(SwitchEntity):
    """Representation of a switch."""

    def __init__(self, hass, name, topic):
        self.hass = hass
        self._name = name
        self._state = False
        self._topic = topic

    @property
    def name(self):
        """Return the name of the switch."""
        return self._name

    @property
    def is_on(self):
        """Return true if the switch is on."""
        return self._state

    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        self._state = True
        await self._publish_mqtt(1, json.dumps({"valve": True}))
        self.schedule_update_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        self._state = False
        await self._publish_mqtt(0, json.dumps({"valve": False}))
        self.schedule_update_ha_state()

    async def _publish_mqtt(self, mode, message):
        """Publish a message to the MQTT topic."""
        topic = self._topic
        if mode == 0:
            topic += "/off"
        elif mode == 1:
            topic += "/on"

        await mqtt.async_publish(self.hass, topic, message)


class DemoSwitch(SwitchEntity):
    """Representation of a switch."""

    def __init__(self, hass, name, topic, valve_switch):
        self.hass = hass
        self._name = name
        self._state = False
        self._topic = topic
        self._valve_switch = valve_switch  # Reference to the valve switch
        self._remove_callback = None  # For stopping the demo mode loop

    @property
    def name(self):
        """Return the name of the switch."""
        return self._name

    @property
    def is_on(self):
        """Return true if the switch is on."""
        return self._state

    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        self._state = True
        await self._start_demo_mode()
        self.schedule_update_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        self._state = False
        await self._stop_demo_mode()
        self.schedule_update_ha_state()

    async def _start_demo_mode(self):
        """Start the demo mode, periodically opening and closing the valve."""

        @callback
        async def clean_valve(now):
            """Toggle the valve switch on and off in demo mode."""
            await self._valve_switch.async_turn_on()
            await asyncio.sleep(5)
            await self._valve_switch.async_turn_off()

            _LOGGER.info("Demo Mode: Valve cleaned.")

        # Start the interval to toggle the valve every 30 seconds
        self._remove_callback = async_track_time_interval(
            self.hass, clean_valve, timedelta(seconds=30)
        )

        _LOGGER.info("Demo Mode: Started, toggling every 30 seconds.")

    async def _stop_demo_mode(self):
        """Stop the demo mode."""
        if self._remove_callback:
            self._remove_callback()  # Stop the periodic toggling
            self._remove_callback = None
            _LOGGER.info("Demo Mode: Stopped.")
