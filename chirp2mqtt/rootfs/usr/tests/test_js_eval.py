"""Test the ChirpStack LoRaWAN integration gRPC interface class."""

from tests import common

from .patches import get_size, mqtt
from chirpha.const import BRIDGE_CONF_COUNT, CONF_APPLICATION_ID

def test_codec_prologue_noissues(caplog):
    """Test codec with issues in prologue, no devices to be installed."""

    def run_test_codec_prologue_noissues(config):
        assert get_size("idevices") == mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_devices  ### device count check
        assert get_size("sensors") == mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_sensors * get_size("idevices")  ### sensor count check

    common.chirp_setup_and_run_test(caplog, run_test_codec_prologue_noissues, test_params=dict(devices=1, codec=17))

def test_codec_prologue_issues(caplog):
    """Test codec with issues in prologue, no devices to be installed."""

    def run_test_codec_prologue_issues(config):
        assert get_size("idevices") == mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_devices  ### device count check
        assert get_size("sensors") == mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_sensors * get_size("idevices")  ### sensor count check

    common.chirp_setup_and_run_test(caplog, run_test_codec_prologue_issues, test_params=dict(devices=1, codec=18))

def test_empty_message(caplog):
    """Test empty message procesing."""

    def run_test_empty_message(config):
        dev_eui = "dev_eui0"
        topic = f"application/{config.get(CONF_APPLICATION_ID)}/device/{dev_eui}/event/up"
        msg = b''
        mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).publish(topic, msg)
        empty_msg_count = common.count_messages(topic, None, keep_history=True)
        assert empty_msg_count == 1

    common.chirp_setup_and_run_test(caplog, run_test_empty_message)
    i_sensor_warn = 0
    for record in caplog.records:
        if "Ignoring topic" in record.msg: i_sensor_warn += 1
    assert i_sensor_warn == 1
