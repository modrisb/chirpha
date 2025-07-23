"""Test the ChirpStack LoRaWAN integration initilization path initiated from start.py."""
import logging
import time
from tests import common

from .patches import get_size, mqtt, set_size
from tests.common import NO_APP_CONFIGURATION_FILE, MIN_SLEEP
from chirpha.const import WARMSG_APPID_WRONG

def test_entry_setup_unload(caplog):
    """Test if integration unloads with default configuration."""

    common.chirp_setup_and_run_test(caplog, None)

def test_grpc_connection_failure(caplog):
    """Test app exits in case of grpc failure."""

    common.chirp_setup_and_run_test(caplog, None, test_params=dict(grpc=0), a_live_at_end=False)

def test_setup_with_no_tenants(caplog):
    """Test if missing tenant has been creted and app is up."""

    common.chirp_setup_and_run_test(caplog, None, test_params=dict(tenants=0), a_live_at_end=True, conf_file=NO_APP_CONFIGURATION_FILE, allowed_msg_level=logging.WARNING)
    i_sensor_warn = 0
    i_sensor_ten = 0
    for record in caplog.records:
        if record.msg == WARMSG_APPID_WRONG: i_sensor_warn += 1
        if "Tenant '" in record.msg: i_sensor_ten += 1
    assert i_sensor_warn == 1 and i_sensor_ten == 1

def test_setup_with_autoselected_tenant_no_apps(caplog):
    """Test if integration unloads with default configuration."""

    common.chirp_setup_and_run_test(caplog, None, test_params=dict(tenants=1, applications=0), a_live_at_end=True, conf_file=NO_APP_CONFIGURATION_FILE, allowed_msg_level=logging.WARNING)
    i_sensor_warn = 0
    i_sensor_app = 0
    for record in caplog.records:
        if record.msg == WARMSG_APPID_WRONG: i_sensor_warn += 1
        if "Application '" in record.msg: i_sensor_app += 1
    assert i_sensor_warn == 1 and i_sensor_app == 1

def test_setup_with_tenant_selection_no_apps(caplog):
    """Test if integration unloads with default configuration."""

    common.chirp_setup_and_run_test(caplog, None, test_params=dict(applications=0), a_live_at_end=True, allowed_msg_level=logging.WARNING)
    i_sensor_warn = 0
    i_sensor_app = 0
    for record in caplog.records:
        if record.msg == WARMSG_APPID_WRONG: i_sensor_warn += 1
        if "Application '" in record.msg: i_sensor_app += 1
    assert i_sensor_warn == 1 and i_sensor_app == 1

def test_setup_with_auto_tenant_auto_apps(caplog):
    """Test if integration unloads with default configuration."""

    common.chirp_setup_and_run_test(caplog, None, test_params=dict(tenants=1, applications=1), a_live_at_end=True, conf_file=NO_APP_CONFIGURATION_FILE, allowed_msg_level=logging.WARNING)
    i_sensor_warn = 0
    for record in caplog.records:
        if record.msg == WARMSG_APPID_WRONG: i_sensor_warn += 1
    assert i_sensor_warn == 1

def test_setup_with_auto_tenant_apps_selection(caplog):
    """Test if integration unloads with default configuration."""

    common.chirp_setup_and_run_test(caplog, None, test_params=dict(tenants=1, applications=2), a_live_at_end=True, conf_file=NO_APP_CONFIGURATION_FILE, allowed_msg_level=logging.WARNING)
    i_sensor_warn = 0
    for record in caplog.records:
        if record.msg == WARMSG_APPID_WRONG: i_sensor_warn += 1
    assert i_sensor_warn == 1

def test_setup_with_auto_tenant_auto_apps_mqtt_fail(caplog):
    """Test if chirpha gracefully exits in case of mqtt connection failure."""

    common.chirp_setup_and_run_test(caplog, None, test_params=dict(tenants=1, mqtt=0), a_live_at_end=False)
    assert "Chirp failed:" in caplog.text

def test_setup_with_auto_tenant_auto_apps_mqtt(caplog):
    """Test if integration unloads with default configuration."""

    common.chirp_setup_and_run_test(caplog, None, test_params=dict(tenants=1), a_live_at_end=True)

def test_thread_kill(caplog):
    """Test forced exit from chirpha."""

    def run_test_thread_kill(config):
        set_size(codec=7)
        common.reload_devices(config)
        assert get_size("devices") * get_size("sensors") == mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_sensors

    common.chirp_setup_and_run_test(caplog, run_test_thread_kill, kill_at_end=True)
    assert "Shutdown requested" in caplog.text

def test_setup_with_failing_mqtt_publish(caplog):
    """Test if chirpha gracefully exits in case of mqtt publish failure."""

    common.chirp_setup_and_run_test(caplog, None, test_params=dict(publish=0), a_live_at_end=False, check_msg_queue=False)
    assert "Chirp failed:" in caplog.text

def test_setup_with_failing_mqtt_subscribe(caplog):
    """Test if chirpha gracefully exits in case of mqtt subscribe failure."""

    common.chirp_setup_and_run_test(caplog, None, test_params=dict(subscribe=0), a_live_at_end=False, check_msg_queue=False)
    assert "Chirp failed:" in caplog.text

def test_setup_with_failing_mqtt_unsubscribe(caplog):
    """Test if chirpha gracefully exits in case of mqtt unsubscribe failure."""

    def run_test_setup_with_failing_mqtt_unsubscribe(config):
        time.sleep(MIN_SLEEP)

    common.chirp_setup_and_run_test(caplog, run_test_setup_with_failing_mqtt_unsubscribe, test_params=dict(unsubscribe=0), a_live_at_end=False, check_msg_queue=False)
    assert "Chirp failed:" in caplog.text
