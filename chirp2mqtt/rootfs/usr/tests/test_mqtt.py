"""Test the ChirpStack LoRa integration MQTT integration class."""

import time
import logging

from chirpha.const import BRIDGE_CONF_COUNT, CONF_APPLICATION_ID, WARMSG_DEVCLS_REMOVED
from tests import common

from .patches import get_size, mqtt, set_size
from tests.common import PAYLOAD_PRINT_CONFIGURATION_FILE, REGULAR_CONFIGURATION_FILE

def test_extended_debug_level(caplog):
    """Test run with extended debug enabled."""

    def run_test_level_names_with_indexes(config):
        common.reload_devices(config)
        assert mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_devices == get_size("idevices")
        assert mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_sensors == get_size("idevices") * get_size("sensors")

    common.chirp_setup_and_run_test(caplog, run_test_level_names_with_indexes, conf_file=PAYLOAD_PRINT_CONFIGURATION_FILE)
    i_sensor_warn = 0
    for record in caplog.records:
        if record.levelno < logging.DEBUG and "MQTT message" in record.msg: i_sensor_warn += 1;
    assert i_sensor_warn > 0

def test_extended_debug_level_off(caplog):
    """Test run with extended debug enabled."""

    def run_test_extended_debug_level_off(config):
        common.reload_devices(config)
        assert mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_devices == get_size("idevices")
        assert mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_sensors == get_size("idevices") * get_size("sensors")

    common.chirp_setup_and_run_test(caplog, run_test_extended_debug_level_off)
    i_sensor_warn = 0
    for record in caplog.records:
        if record.levelno == logging.DEBUG and "MQTT message" in record.msg: i_sensor_warn += 1
    assert i_sensor_warn == 0

def test_level_names_with_indexes(caplog):
    """Test run with values description with indexes."""
    def run_test_level_names_with_indexes(config):
        indexed_configs = common.count_messages(r'/config$', r'"value_template":\s*"{{\s*value_json\..*\[.*\]\s*}}"', keep_history=False)
        assert indexed_configs == 2

    common.chirp_setup_and_run_test(caplog, run_test_level_names_with_indexes, test_params=dict(devices=1, codec=5))

def test_values_template_default(caplog):
    """Test if default value_template is added to configuration."""
    def run_test_values_template_default(config):
        indexed_configs = common.count_messages(r'/config$', r'value_json.object.counter', keep_history=False)
        assert indexed_configs == 1

    common.chirp_setup_and_run_test(caplog, run_test_values_template_default, test_params=dict(devices=1, codec=6))


def test_explicit_integration_setting(caplog):
    """Test run with explicit integration set in codec js."""
    def run_test_explicit_integration_setting(config):
        indexed_configs = common.count_messages(r'/climate/.*/config$', None, keep_history=False)
        assert indexed_configs == 1

    common.chirp_setup_and_run_test(caplog, run_test_explicit_integration_setting, test_params=dict(devices=1, codec=7))


def test_no_device_class(caplog):
    """Test run with no explicit device class set in codec js."""
    def run_test_no_device_class(config):
        indexed_configs = common.count_messages(r'/sensor/.*/config$', r"device_class", keep_history=False)
        assert indexed_configs == 0

    common.chirp_setup_and_run_test(caplog, run_test_no_device_class, test_params=dict(devices=1, codec=8))


def test_wrong_device_class(caplog):
    """Test run with unknown device class set in codec js."""
    def run_test_wrong_device_class(config):
        indexed_configs = common.count_messages(r'/sensor/.*/config$', None, keep_history=False)
        assert indexed_configs == 1
        indexed_configs = common.count_messages(r'/sensor/.*/config$', r"device_class", keep_history=False)
        assert indexed_configs == 0

    common.chirp_setup_and_run_test(caplog, run_test_wrong_device_class, test_params=dict(devices=1, codec=9), allowed_msg_level=logging.WARNING)
    i_sensor_warn = 0
    for record in caplog.records:
        if record.msg == WARMSG_DEVCLS_REMOVED: i_sensor_warn += 1
    assert i_sensor_warn == 1

def test_command_topic(caplog):
    """Test run with command topic set in codec js."""
    def run_test_command_topic(config):
        indexed_configs = common.count_messages(r'/config$', r'"command_topic".*/down', keep_history=False)
        assert indexed_configs == 1

    common.chirp_setup_and_run_test(caplog, run_test_command_topic, test_params=dict(devices=1, codec=10))


def test_humidifier_dev_class(caplog):
    """Test run with humidifier device class in codec js.."""
    def run_test_humidifier_dev_class(config):
        indexed_configs = common.count_messages(r'/humidifier/.*/config$', None, keep_history=False)
        assert indexed_configs == 1

    common.chirp_setup_and_run_test(caplog, run_test_humidifier_dev_class, test_params=dict(devices=1, codec=15))

def test_enabled_by_default(caplog):
    """Test run with enabled_by_default flag in codec js.."""
    def run_test_enabled_by_default(config):
        messages = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).get_published(keep_history=True)
        print(messages)
        enabled_configs = common.count_messages(r'/config$', '"enabled_by_default": false', keep_history=False)    # to be received as subscribed
        assert enabled_configs == 1

    common.chirp_setup_and_run_test(caplog, run_test_enabled_by_default, test_params=dict(devices=1, codec=22), conf_file=REGULAR_CONFIGURATION_FILE, allowed_msg_level=logging.WARNING)

# to remove retained messages
# mosquitto_pub -h ha -u loramqtt -P ploramqtt -t "application/72a56954-700f-4a52-90d2-86cf76df5c57/bridge/status"  -n -r -d
