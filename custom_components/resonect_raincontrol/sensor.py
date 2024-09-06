from __future__ import annotations  # noqa: D104

import asyncio
import json
import logging
import random

import voluptuous as vol

from datetime import timedelta
from collections import deque

from homeassistant.components import mqtt
from homeassistant.components.sensor import SensorEntity
from homeassistant.components.sensor.const import SensorDeviceClass
from homeassistant.core import HomeAssistant, callback
from homeassistant.const import PERCENTAGE, VOLUME

from .const import DOMAIN, TOPIC

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    """Set up the sensor platform."""
    flow_sensor_1 = MqttSensor(hass, "Water Flow 1", TOPIC, "waterFlow1", 0)
    flow_sum_sensor_1 = MqttSensor(hass, "Water Flow Sum 1", TOPIC, "waterFlowSum1", 4)
    flow_sensor_2 = MqttSensor(hass, "Water Flow 2", TOPIC, "waterFlow2", 0)
    flow_sum_sensor_2 = MqttSensor(hass, "Water Flow Sum 2", TOPIC, "waterFlowSum2", 4)
    current_sensor = MqttSensor(hass, "UV Lamp Current", TOPIC, "sensorCurrent", 1)
    power_sensor = MqttSensor(hass, "UV Lamp Power", TOPIC, "sensorCurrent", 2)
    cumulative_flow_sensor_1 = CumulativeFlowSensor(
        hass, "Cumulative Water Flow 1", TOPIC, "flow1", 3
    )
    cumulative_flow_sensor_2 = CumulativeFlowSensor(
        hass, "Cumulative Water Flow 2", TOPIC, "flow2", 3
    )
    flow_sum_diff = MqttSensor(hass, "Water Flow Sum Difference", TOPIC, "waterFlowSum2", 4)

    async_add_entities(
        [
            flow_sensor_1,
            flow_sensor_2,
            current_sensor,
            power_sensor,
            cumulative_flow_sensor_1,
            cumulative_flow_sensor_2,
            flow_sum_sensor_1,
            flow_sum_sensor_2,
            flow_sum_diff
        ],
        update_before_add=True,
    )


class MqttSensor(SensorEntity):
    """Representation of a sensor."""

    def __init__(self, hass, name, topic, parameter, device_class):
        self.hass = hass
        self._unique_id = f"{DOMAIN}_{name.lower().replace(' ', '_')}"
        self._name = name
        self._state = None
        self._topic = topic
        self._unsubscribe = None
        self._flow_parameter = parameter
        if device_class == 0:
            self.native_unit_of_measurement = "l/min"
        elif device_class == 1:
            self.native_unit_of_measurement = "A"
        elif device_class == 2:
            self.native_unit_of_measurement = "W"
        elif device_class == 3:
            self.native_unit_of_measurement = "l/h"
        elif device_class == 4:
            self.native_unit_of_measurement = "l"

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    async def async_added_to_hass(self):
        """Subscribe to MQTT events when added to hass."""

        @callback
        def message_received(msg):
            """Handle new MQTT messages."""
            try:
                payload_dict = json.loads(msg.payload)
                flow = payload_dict.get(self._flow_parameter)

                # Update the state of the sensor (e.g., using flow1 for this example)
                if self._name == ("UV Lamp Power"):
                    if flow > 0.2:
                        self._state = round(55 + random.uniform(-2, 2),2)
                    else:
                        self._state = 0
                elif self._name == ("Water Flow Sum Difference"):
                    sum1 = payload_dict.get("waterFlowSum1")
                    sum2 = payload_dict.get("waterFlowSum2")

                    self._state = sum2 - sum1
                else:
                    self._state = flow

                # Optionally, update other entities if needed
                # hass.states.async_set(entity_flow2, flow2)
                # hass.states.async_set(entity_current, current)

                # Notify Home Assistant of state change
                self.async_write_ha_state()

            except json.JSONDecodeError:
                # Log error if necessary
                _LOGGER.error("Failed to decode JSON payload from MQTT message")

        # Subscribe to the topic
        self._unsubscribe = await mqtt.async_subscribe(
            self.hass, self._topic, message_received
        )

    async def async_will_remove_from_hass(self):
        """Unsubscribe from MQTT events when removed from hass."""
        if self._unsubscribe is not None:
            self._unsubscribe()


class CumulativeFlowSensor(MqttSensor):
    """Representation of a sensor that accumulates water flow over 1 hour."""

    def __init__(self, hass, name, topic, parameter, device_class):
        super().__init__(hass, name, topic, parameter, device_class)
        self._cumulative_flow = 0
        self._hourly_flow = deque(maxlen=3600)  # Store 3600 seconds of data
        self._last_update = None

    @property
    def state(self):
        """Return the cumulative state of the sensor."""
        return self._cumulative_flow

    async def async_added_to_hass(self):
        """Subscribe to MQTT events and handle hourly accumulation."""
        await super().async_added_to_hass()

        @callback
        def message_received(msg):
            """Handle new MQTT messages for cumulative flow."""
            try:
                payload_dict = json.loads(msg.payload)
                flow = payload_dict.get(self._flow_parameter, 0)

                # Update the deque with the current flow value
                self._hourly_flow.append(flow)

                # Calculate the cumulative flow over the last hour
                self._cumulative_flow = sum(self._hourly_flow)

                # Notify Home Assistant of state change
                self.async_write_ha_state()

            except json.JSONDecodeError:
                _LOGGER.error("Failed to decode JSON payload from MQTT message")

        # Subscribe to the topic for cumulative flow
        self._unsubscribe = await mqtt.async_subscribe(
            self.hass, self._topic, message_received
        )
