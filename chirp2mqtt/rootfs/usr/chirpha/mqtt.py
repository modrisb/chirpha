"""The Chirpstack LoRaWan integration - mqtt interface."""
from __future__ import annotations

import datetime
import json
import logging
import re
import hashlib
import threading
import time
from zoneinfo import ZoneInfo

import paho.mqtt.client as mqtt

from .const import (
    BRIDGE,
    BRIDGE_ENTITY_NAME,
    BRIDGE_NAME,
    BRIDGE_RESTART_ID,
    BRIDGE_RESTART_NAME,
    BRIDGE_STATE_ID,
    BRIDGE_VENDOR,
    CONF_APPLICATION_ID,
    CONF_MQTT_DISC,
    CONF_MQTT_PORT,
    CONF_MQTT_PWD,
    CONF_MQTT_SERVER,
    CONF_MQTT_USER,
    CONF_OPTIONS_DEBUG_PAYLOAD,
    CONF_OPTIONS_RESTORE_AGE,
    CONF_OPTIONS_START_DELAY,
    CONNECTIVITY_DEVICE_CLASS,
    ENTITY_CATEGORY_DIAGNOSTIC,
    CONF_APPLICATION_ID,
    CONF_MQTT_SERVER,
    CONF_MQTT_PORT,
    CONF_MQTT_DISC,
    WARMSG_DEVCLS_REMOVED,
)
from .grpc import ChirpGrpc

_LOGGER = logging.getLogger(__name__)

UTC_TIMEZONE = ZoneInfo("UTC")


def to_lower_case_no_blanks(e_name):
    """Change string to lower case and replace blanks with _ ."""
    return e_name.lower().replace(" ", "_")

def generate_unique_id(configuration):
    """Create untegration unique id based on api/mqtt servers configurations."""
    u_id = "".join(
        [
            str(configuration[id_key])
            for id_key in (
                CONF_APPLICATION_ID,
                CONF_MQTT_SERVER,
                CONF_MQTT_PORT,
                CONF_MQTT_DISC,
            )
        ]
    )
    unique_id = f"{hashlib.md5(u_id.encode('utf-8')).hexdigest()}"
    return unique_id

def convert_ret_val(ret_val):
    if isinstance(ret_val, tuple):
        if ret_val[0]:
            return f", return code ({ret_val[0]},{ret_val[1]})"
        else:
            return ""
    else:
        if ret_val.rc:
            return f", return code ({ret_val.rc},{ret_val.mid})"
        else:
            return ""

class ChirpToHA:
    """Chirpstack LoRaWan MQTT interface."""

    def __init__(
        self, config, version, classes, grpc_client: ChirpGrpc
    ) -> None:
        """Open connection to HA MQTT server and initialize internal variables."""
        self._config = config
        self._version = version
        self._application_id = grpc_client._application_id
        self._unique_id = generate_unique_id(self._config)
        self._grpc_client: ChirpGrpc = grpc_client
        self._host = self._config.get(CONF_MQTT_SERVER)
        self._port = self._config.get(CONF_MQTT_PORT)
        self._user = self._config.get(CONF_MQTT_USER)
        self._pwd = self._config.get(CONF_MQTT_PWD)
        self._classes = classes
        self._dev_sensor_count = 0
        self._dev_count = 0
        self._last_update = None
        self._discovery_prefix = self._config.get(CONF_MQTT_DISC)
        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

        self._client.on_connect = self.on_connect
        self._client.username_pw_set(self._user, self._pwd)
        self._client.connect(self._host, self._port)
        self._origin = {
            "name": BRIDGE_VENDOR,
            "sw_version": self._version,
        }
        self._bridge_indentifier = to_lower_case_no_blanks(
            f"{BRIDGE_VENDOR} {BRIDGE} {self._unique_id}"
        )
        self._ha_online_event = threading.Event()
        self._bridge_init_time = None
        self._cur_open_time = None
        self._discovery_delay = self._config.get(CONF_OPTIONS_START_DELAY)
        self._cur_age = self._config.get(CONF_OPTIONS_RESTORE_AGE)
        self._devices_config_topics = set()
        self._old_devices_config_topics = set()
        self._messages_to_restore_values = []
        self._top_level_msg_names = None
        self._values_cache = {}
        self._config_topics_published = 0
        self._bridge_config_topics_published = -1
        self._initialize_topic = f"application/{self._application_id}/status"
        self._bridge_state_topic = f"application/{self._application_id}/bridge/status"
        self._bridge_restart_topic = (
            f"application/{self._application_id}/bridge/restart"
        )
        self._ha_status = f"{self._discovery_prefix}/status"
        self._sub_cur_topic = f"application/{self._application_id}/device/+/event/cur"
        self._print_payload = self._config.get(CONF_OPTIONS_DEBUG_PAYLOAD)
        _LOGGER.info(
            "Connected to MQTT at %s:%s as %s",
            self._config.get(CONF_MQTT_SERVER),
            self._config.get(CONF_MQTT_PORT),
            self._config.get(CONF_MQTT_USER),
        )
        self._client.on_message = self.on_message

        self._client.subscribe(self._initialize_topic)
        self._client.subscribe(self._ha_status)
        self._availability_element = [
            {
                "topic": self._bridge_state_topic,
                "value_template": "{{ value_json.state }}",
                "payload_available": "online",
                "payload_not_available": "offline",
            }
        ]

        self._wait_for_ha_online = threading.Thread(target=self.ha_online_waiter)

        ret_val = self._client.publish( self._initialize_topic, "initialize" )
        _LOGGER.info(
            "Bridge setup 'initialize' message published%s",
            convert_ret_val(ret_val),
        )

    def on_connect(self, client, userdata, connect_flags, reason_code, properties):
        if reason_code.is_failure:
            raise Exception(f"MQTT connection failed: {reason_code.value} - '{reason_code}'")
        else:
            self._client.on_connect = None

    def ha_online_waiter(self): # to start bridge if homeassistant/status message is not received within discovery timeout
        if not self._ha_online_event.wait(self._discovery_delay+0.1):
            self._ha_online_event.set()
            ret_val = self._client.publish( self._initialize_topic, "configure" )
            _LOGGER.debug("%s timeout expired, but no HA online message received, bridge setup 'configure' message published%s",
                          self._discovery_delay, convert_ret_val(ret_val))

    def start_bridge(self):
        """Start Lora bridge registration within HA MQTT."""
        _LOGGER.info(
            "Bridge initialization time stamp set to %s",
            self._bridge_init_time,
        )
        bridge_publish_data = self.get_conf_data(
            BRIDGE_STATE_ID,
            {  #   'entities':
                "entity_conf": {
                    "state_topic": self._bridge_state_topic,
                    "value_template": "{{ value_json.state }}",
                    "object_id": to_lower_case_no_blanks(
                        f"{BRIDGE_VENDOR} {BRIDGE} {BRIDGE_ENTITY_NAME}"
                    ),
                    "unique_id": to_lower_case_no_blanks(
                        f"{BRIDGE} {self._unique_id} {BRIDGE_ENTITY_NAME} {BRIDGE_VENDOR}"
                    ),
                    "device_class": CONNECTIVITY_DEVICE_CLASS,
                    "entity_category": ENTITY_CATEGORY_DIAGNOSTIC,
                    "payload_on": "online",
                    "payload_off": "offline",
                },
            },
            {  #   'device':
                "manufacturer": BRIDGE_VENDOR,
                "model": BRIDGE,
                "identifiers": [to_lower_case_no_blanks(self._bridge_indentifier)],
            },
            {  #   'dev_conf':
                "measurement_names": {BRIDGE_STATE_ID: BRIDGE_ENTITY_NAME},
                "dev_name": BRIDGE_NAME,
                "dev_eui": self._unique_id,
            },
        )

        ret_val = self._client.publish(
            bridge_publish_data["discovery_topic"],
            bridge_publish_data["discovery_config"],
            retain=True,
        )
        _LOGGER.debug(
            "Bridge device configuration published%s",
            convert_ret_val(ret_val),
        )
        if self._print_payload:
            _LOGGER.debug(
                "Bridge device configuration published. MQTT payload %s",
                bridge_publish_data["discovery_config"],
            )
        self._bridge_config_topics_published = 1

        bridge_refresh_data = self.get_conf_data(
            BRIDGE_RESTART_ID,
            {  #   'entities':
                "integration": "button",
                "entity_conf": {
                    "availability_mode": "all",
                    "state_topic": "{None}",
                    "command_topic": self._bridge_restart_topic,
                    "object_id": to_lower_case_no_blanks(
                        f"{BRIDGE_VENDOR} {BRIDGE} {BRIDGE_RESTART_ID}"
                    ),
                    "unique_id": to_lower_case_no_blanks(
                        f"{BRIDGE} {self._unique_id} {BRIDGE_RESTART_NAME} {BRIDGE_VENDOR}"
                    ),
                    "device_class": "restart",
                    "payload_press": "",
                },
            },
            {  #   'device':
                "manufacturer": BRIDGE_VENDOR,
                "model": BRIDGE,
                "identifiers": [to_lower_case_no_blanks(self._bridge_indentifier)],
            },
            {  #   'dev_conf':
                "measurement_names": {BRIDGE_RESTART_ID: BRIDGE_RESTART_NAME},
                "dev_name": BRIDGE_NAME,
                "dev_eui": self._unique_id,
            },
        )
        ret_val = self._client.publish(
            bridge_refresh_data["discovery_topic"],
            bridge_refresh_data["discovery_config"],
            retain=True,
        )
        self._bridge_config_topics_published += 1
        ret_val = self._client.publish(
            self._bridge_state_topic, '{"state": "online"}', retain=True
        )
        _LOGGER.info(
            "Bridge state turned on%s",
            convert_ret_val(ret_val),
        )

    def reload_devices(self):
        self._bridge_init_time = time.time()

        device_sensors = self._grpc_client.get_current_device_entities()

        self._dev_sensor_count = 0
        self._dev_count = 0

        self._devices_config_topics = set()
        devices_config_topics = set()
        self._config_topics_published = 0
        self._values_cache = {}
        self._messages_to_restore_values = []
        value_templates = []

        for device in device_sensors:
            previous_values = device["dev_conf"].get("prev_value")
            dev_eui = device["dev_conf"]["dev_eui"]
            self._values_cache[dev_eui] = {}
            for sensor in device["entities"]:
                sensor_entity_conf_data = self.get_conf_data(
                    sensor,
                    device["entities"][sensor],
                    device["device"],
                    device["dev_conf"],
                )
                for conf_key in sensor_entity_conf_data["discovery_config_struct"].keys():
                    if conf_key.endswith("_template"):
                        value_templates.append(sensor_entity_conf_data["discovery_config_struct"][conf_key])
                devices_config_topics.add(sensor_entity_conf_data["discovery_topic"])
                ret_val = self._client.publish(
                    sensor_entity_conf_data["discovery_topic"],
                    sensor_entity_conf_data["discovery_config"],
                    retain=True,
                )
                _LOGGER.info(
                    f"Discovery message published: device {dev_eui} sensor '{sensor_entity_conf_data["discovery_topic"].split("/")[1]}'%s",
                    convert_ret_val(ret_val),
                )
                if self._print_payload:
                    _LOGGER.debug(
                        "Device sensor published. MQTT payload %s",
                        sensor_entity_conf_data["discovery_config"],
                    )
                for sens_id in previous_values:
                    if (
                        sens_id
                        in device["entities"][sensor]["entity_conf"]["value_template"]
                    ):
                        topic_for_value = sensor_entity_conf_data["status_topic"]
                        payload_for_value = f'{{"{sens_id}":{str(previous_values[sens_id])},"time_stamp":{time.time()}}}'
                        self._messages_to_restore_values.append(
                            (topic_for_value, payload_for_value)
                        )
                self._dev_sensor_count += 1
            self._dev_count += 1

        self._devices_config_topics = devices_config_topics

        self._top_level_msg_names = {}
        for value_template in value_templates:
            for msg_name in re.findall(r"(value_json\..{1,}?)\ ", value_template):
                names = re.split(r"\.", msg_name[11:])
                level = self._top_level_msg_names
                for name in names:
                    name_t = re.split(r"\[", name)
                    if len(name_t) == 1:
                        if name not in level:
                            level[name] = {}
                        level = level[name]
                    else:
                        if name_t[0] not in level:
                            level[name_t[0]] = [{}]
                        level = level[name_t[0]][0]
        _LOGGER.debug("Top level names %s", self._top_level_msg_names)

        _LOGGER.info(
            "%s value(s) restore request(s) queued", len(self._messages_to_restore_values)
        )
        _LOGGER.info(
            "Devices reloaded, %s device{s) and %s sensor(s) found",
            self._dev_count,
            self._dev_sensor_count,
        )

    def clean_up_disappeared(self):
        """Remove retained config messages from mqtt server if not in recent device list."""
        if self._old_devices_config_topics:
            for config_topic in (
                self._old_devices_config_topics - self._devices_config_topics
            ):
                ret_val = self._client.publish(config_topic, None, retain=True)
                _LOGGER.info(
                    "Removing retained topic %s%s", config_topic, convert_ret_val(ret_val)
                )
        self._old_devices_config_topics = self._devices_config_topics
        self._config_topics_published = 0

    def on_message(self, client, userdata, message):
        """Process subscribed messages."""
        self._last_update = datetime.datetime.now(UTC_TIMEZONE)
        if message.topic == self._bridge_state_topic:
            _LOGGER.info("Bridge status message received, retain=%s ", message.retain)
        elif message.topic == self._bridge_restart_topic:
            _LOGGER.info(
                "Restart requested, starting devices re-registration (retain=%s).",
                message.retain,
            )
            self._bridge_config_topics_published = 0    # enables value restoration
            self.reload_devices()
        elif message.topic == self._ha_status:
            payload = message.payload.decode("utf-8")
            if payload == "online":
                self._ha_online_event.set()
                ret_val = self._client.publish( self._initialize_topic, "configure" )
                _LOGGER.info(
                    "HA online, publishing bridge setup 'configure' message (retain=%s)",
                    message.retain,
                )
            elif payload == "offline":
                _LOGGER.info(
                    "HA offline message received, ready for re-initialization.",
                )

        elif message.topic == self._initialize_topic:
            payload = message.payload.decode("utf-8")
            _LOGGER.info(
                "Bridge setup '%s' message received",
                payload
            )
            if payload == "initialize":
                self._wait_for_ha_online.start()
            else: # configure
                self._client.subscribe(self._bridge_state_topic)
                self._client.subscribe(self._bridge_restart_topic)
                self._client.subscribe(
                    f"application/{self._application_id}/device/+/event/up"
                )
                self._client.subscribe(f"{self._discovery_prefix}/+/+/+/config")
                self.start_bridge()
                self.reload_devices()
        else:
            subtopics = message.topic.split("/")
            payload = message.payload.decode("utf-8")
            payload_struct = json.loads(payload) if len(payload) > 2 else None
            if payload_struct:
                time_stamp = payload_struct.get("time_stamp")
                if subtopics[-1] == "config":
                    if (
                        "via_device" in payload_struct["device"]
                        and payload_struct["device"]["via_device"]
                        == self._bridge_indentifier
                    ):
                        _LOGGER.info(f"Registration message with time stamp {time_stamp} received for device {subtopics[2]} sensor {subtopics[1]}")
                        if self._print_payload:
                            _LOGGER.debug(
                                "MQTT registration message received: MQTT payload %s", payload
                            )
                        self._old_devices_config_topics.add(message.topic)
                        if (
                            time_stamp and float(time_stamp) >= self._bridge_init_time
                        ):
                            self._config_topics_published += 1
                    else:
                        self._bridge_config_topics_published -= 1
                elif subtopics[-1] == "cur":
                    dev_eui = subtopics[-3]
                    _LOGGER.info("Cached values received for device %s", dev_eui)
                    if self._print_payload:
                        _LOGGER.debug("Cached values received MQTT payload %s", payload)
                    _LOGGER.debug(
                        "Cached values payload time %s, bridge time %s, cached object %s, value cache %s",
                        time_stamp,
                        self._bridge_init_time,
                        payload_struct.get("object"),
                        self._values_cache,
                    )
                    if (
                        time_stamp and float(time_stamp) < self._bridge_init_time
                    ):
                        if dev_eui not in self._values_cache:
                            ret_val = self._client.publish(message.topic, None, retain=True)
                            _LOGGER.debug(
                                "Value cache removal topic %s published%s",
                                message.topic,
                                convert_ret_val(ret_val),
                            )
                        elif self._values_cache[dev_eui] == {}:
                            self._values_cache[dev_eui] = self.join_filtered_messages(
                                {}, payload_struct, self._top_level_msg_names
                            )
                            ret_val = self.publish_value_cache_record(
                                subtopics, "up", self._values_cache[dev_eui]
                            )
                    cache_not_retrieved = len(
                        [dev_id for dev_id, val in self._values_cache.items() if val == {}]
                    )
                    _LOGGER.debug("%s devices cached values not processed", cache_not_retrieved)
                    if (
                        time.time() - self._cur_open_time >= self._cur_age
                        or cache_not_retrieved == 0
                    ):
                        ret_val = self._client.unsubscribe(self._sub_cur_topic)
                        _LOGGER.info(
                            "Unsubscribed from retained values topic%s",
                            convert_ret_val(ret_val),
                        )
                        _LOGGER.debug(
                            "Not processed retained devices %s, processing age %s(s)",
                            cache_not_retrieved,
                            time.time() - self._cur_open_time,
                        )
                elif subtopics[-1] == "up":
                    dev_eui = subtopics[-3]
                    if (
                        not time_stamp
                        and dev_eui in self._values_cache
                    ):
                        self._values_cache[dev_eui] = self.join_filtered_messages(
                            self._values_cache[dev_eui],
                            payload_struct,
                            self._top_level_msg_names,
                        )
                        ret_val = self.publish_value_cache_record(
                            subtopics, "cur", self._values_cache[dev_eui], retain=True
                        )
            else:
                _LOGGER.info(
                    "Ignoring topic %s with payload %s",
                    message.topic,
                    message.payload,
                )
        if (
            len(self._devices_config_topics) > 0
            and self._config_topics_published > 0
            and self._config_topics_published >= len(self._devices_config_topics)
        ):
            _LOGGER.info(
                "%s of %s configuration messages received, %s disappeared devices",
                self._config_topics_published,
                len(self._devices_config_topics),
                len(self._old_devices_config_topics - self._devices_config_topics),
            )
            self.clean_up_disappeared()
        if self._bridge_config_topics_published == 0:
            self._bridge_config_topics_published = -1
            time.sleep(self._discovery_delay)
            self._cur_open_time = time.time()
            ret_val = self._client.subscribe(self._sub_cur_topic)
            _LOGGER.info(
                "Subscribed to retained values topic%s",
                convert_ret_val(ret_val),
            )
            for restore_message in self._messages_to_restore_values:
                ret_val = self._client.publish(*restore_message)
                _LOGGER.info(
                    f"Previous sensor values restored for device {restore_message[0].split('/')[3]}%s",
                    convert_ret_val(ret_val),
                )
                if self._print_payload:
                    _LOGGER.debug(
                        "Previous sensor values restored. MQTT payload %s",
                        restore_message[1],
                    )
            self._messages_to_restore_values = []

    def publish_value_cache_record(
        self, topic_array, topic_suffix, payload_struct, retain=False
    ):
        """Publish sensor value to values cache message."""
        topic_int = topic_array.copy()
        topic_int[-1] = topic_suffix
        payload_struct["time_stamp"] = time.time()
        publish_topic = "/".join(topic_int)
        ret_val = self._client.publish(
            publish_topic, json.dumps(payload_struct), retain=retain
        )
        _LOGGER.debug(
            f"Cached values published for device {publish_topic.split("/")[3]}%s",
            convert_ret_val(ret_val),
        )
        if self._print_payload:
            _LOGGER.debug(
                "Cached values related MQTT payload %s published with code %s",
                payload_struct,
                convert_ret_val(ret_val),
            )
        return ret_val

    def join_filtered_messages(self, message_o, message_n, levels_filter):
        """Join 2 payloads keeping all level data and recent values from message_n."""
        if isinstance(levels_filter, list):
            filtered = [{}]
            for level_filter in levels_filter[0]:
                message_o_r = message_o[0].get(level_filter) if message_o else None
                message_n_r = message_n[0].get(level_filter) if message_n else None
                if not message_o_r and not message_n_r:
                    continue
                filtered[0][level_filter] = self.join_filtered_messages(
                    message_o_r, message_n_r, levels_filter[0].get(level_filter)
                )
        elif levels_filter == {}:
            filtered = message_n if message_n else message_o
        else:
            filtered = {}
            for level_filter in levels_filter:
                message_o_r = message_o.get(level_filter) if message_o else None
                message_n_r = message_n.get(level_filter) if message_n else None
                if not message_o_r and not message_n_r:
                    continue
                filtered[level_filter] = self.join_filtered_messages(
                    message_o_r, message_n_r, levels_filter.get(level_filter)
                )
        return filtered

    def get_discovery_topic(self, dev_id, sensor, device, dev_conf):
        """Prepare sensor discovery topic based on integration type/device class."""
        if not sensor.get("integration"):
            mqtt_integration = None
            device_class = sensor["entity_conf"].get("device_class")
            if device_class:
                for integration in self._classes["integrations"]:
                    if device_class in self._classes.get(integration):
                        mqtt_integration = integration
                        break
                if not mqtt_integration:
                    mqtt_integration = "sensor"
                    _LOGGER.warning(
                        WARMSG_DEVCLS_REMOVED,
                        device_class,
                        dev_conf["dev_eui"],
                    )
                    del sensor["entity_conf"]["device_class"]
            else:
                mqtt_integration = "sensor"
                _LOGGER.info(
                    "No device class set for dev_eui %s/%s and no integration specified, set to 'sensor'",
                    dev_conf["dev_eui"],
                    dev_id,
                )
        else:
            mqtt_integration = sensor.get("integration")
        return f"{self._discovery_prefix}/{mqtt_integration}/{dev_conf['dev_eui']}/{dev_id}/config"

    def get_conf_data(self, dev_id, sensor, device, dev_conf):
        """Prepare discovery payload."""
        discovery_topic = self.get_discovery_topic(dev_id, sensor, device, dev_conf)
        status_topic = f"application/{self._application_id}/device/{dev_conf['dev_eui']}/event/{sensor.get('data_event') if sensor.get('data_event') else 'up'}"
        comand_topic = f"application/{self._application_id}/device/{dev_conf['dev_eui']}/command/down"
        discovery_config = sensor["entity_conf"].copy()
        discovery_config["device"] = device.copy()
        discovery_config["device"]["name"] = (
            dev_conf["dev_name"] if dev_conf["dev_name"] else "0x" + dev_conf["dev_eui"]
        )
        if not device.get("identifiers"):
            discovery_config["device"]["identifiers"] = [
                to_lower_case_no_blanks(BRIDGE_VENDOR + "_" + dev_conf["dev_eui"])
            ]
            discovery_config["device"]["via_device"] = self._bridge_indentifier
            discovery_config["availability"] = self._availability_element
        discovery_config["origin"] = self._origin
        if not discovery_config.get("state_topic"):
            discovery_config["state_topic"] = status_topic
        discovery_config["name"] = (
            dev_conf["measurement_names"][dev_id]
            if dev_conf["measurement_names"].get(dev_id)
            else dev_id
        )
        if not discovery_config.get("unique_id"):
            discovery_config["unique_id"] = to_lower_case_no_blanks(
                BRIDGE_VENDOR + "_" + dev_conf["dev_eui"] + "_" + dev_id
            )
        if not discovery_config.get("object_id"):
            discovery_config["object_id"] = to_lower_case_no_blanks(
                dev_conf["dev_eui"] + "_" + dev_id
            )
        discovery_config_enum = discovery_config.copy()
        for key, value in discovery_config_enum.items():
            if not isinstance(value, str):
                continue
            if value == "{None}":
                del discovery_config[key]
            if value == "{command_topic}":
                discovery_config[key] = comand_topic
            if value == "{status_topic}":
                discovery_config[key] = status_topic
            if "{dev_eui}" in value:
                discovery_config[key] = value.replace( "{dev_eui}", dev_conf["dev_eui"] )
        discovery_config["enabled_by_default"] = True
        discovery_config["time_stamp"] = self._bridge_init_time
        return {
            "discovery_config_struct": discovery_config,
            "discovery_config": json.dumps(discovery_config),
            "discovery_topic": discovery_topic,
            "status_topic": status_topic,
            "comand_topic": comand_topic,
        }

    def close(self):
        """Close recent session."""
        self._client.disconnect()
