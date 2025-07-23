"""Test the ChirpStack LoRaWAN integration gRPC interface class."""

from tests import common
import logging
from unittest import mock

from .patches import get_size, mqtt, set_size, dukpy
from chirpha.const import ERRMSG_CODEC_ERROR, ERRMSG_DEVICE_IGNORED

def test_faulty_codec(caplog):
    """Test faulty codec - devices are not installed."""

    common.chirp_setup_and_run_test(caplog, common.check_for_no_registration, test_params=dict(devices=1, codec=3), allowed_msg_level=logging.ERROR)
    i_sensor_err1 = 0
    i_sensor_err2 = 0
    for record in caplog.records:
        if record.msg == ERRMSG_CODEC_ERROR: i_sensor_err1 += 1
        if record.msg == ERRMSG_DEVICE_IGNORED: i_sensor_err2 += 1
    assert i_sensor_err1 == 1 and i_sensor_err2 == 1

@mock.patch("chirpha.grpc.dukpy", new=dukpy)
def test_faulty_json(caplog):
    """Test faulty codec json: conversion to json mocked false making descriptor ignored """
    common.chirp_setup_and_run_test(caplog, common.check_for_no_registration, test_params=dict(devices=1, codec=19), allowed_msg_level=logging.ERROR)
    i_sensor_err = 0
    for record in caplog.records:
        if record.msg == ERRMSG_DEVICE_IGNORED: i_sensor_err += 1
    assert i_sensor_err == 1

def test_codec_with_single_q_strings(caplog):
    """Test codec with ' as string encloser - devices to be installed."""
    def run_test_codec_with_single_q_strings(config):
        msg_count = common.count_messages(r'/config$', r'vendor0', keep_history=True)
        assert msg_count == 1
        msg_count = common.count_messages(r'/config$', r'model1', keep_history=True)
        assert msg_count == 1
        msg_count = common.count_messages(r'/config$', r'{{ value_json.object.counter }}', keep_history=True)
        assert msg_count == 1

    common.chirp_setup_and_run_test(caplog, run_test_codec_with_single_q_strings, test_params=dict(devices=1, codec=16) )

def test_with_devices_disabled(caplog):
    """Test disabled devices are listed - no devices to be installed."""

    common.chirp_setup_and_run_test(caplog, common.check_for_no_registration, test_params=dict(disabled=True))

def test_codec_prologue_issues(caplog):
    """Test codec with issues in prologue, no devices to be installed."""

    def run_test_codec_prologue_issues(config):
        common.check_for_no_registration(config)
        set_size(devices=1, codec=12)  # return statement missing
        common.reload_devices(config)
        assert get_size("idevices") == mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_devices  ### device count check
        assert get_size("sensors") == mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_sensors * get_size("idevices")  ### sensor count check
        common.check_for_no_registration(config)
        set_size(devices=1, codec=13)  # } after return statement missing
        common.reload_devices(config)
        assert get_size("idevices") == mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_devices  ### device count check
        assert get_size("sensors") == mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_sensors * get_size("idevices")  ### sensor count check
        common.check_for_no_registration(config)

    common.chirp_setup_and_run_test(caplog, run_test_codec_prologue_issues, test_params=dict(devices=1, codec=11), allowed_msg_level=logging.ERROR)
    i_sensor_err1 = 0
    i_sensor_err2 = 0
    for record in caplog.records:
        if record.msg == ERRMSG_CODEC_ERROR: i_sensor_err1 += 1
        if record.msg == ERRMSG_DEVICE_IGNORED: i_sensor_err2 += 1
    assert i_sensor_err1 == 2 and i_sensor_err2 == 3

def test_codec_with_comment(caplog):
    """Test codec with comments in body."""

    def run_test_codec_with_comment(config):
        sensor_configs = common.count_messages(r'/config$', r'"via_device": "chirp2mqtt_bridge_', keep_history=False)
        assert sensor_configs == 1
        set_size(devices=1, codec=14)  # incorrect comment, codec should fail
        common.reload_devices(config)
        assert get_size("idevices") == mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_devices  ### device count check
        assert get_size("sensors") == mqtt.Client(mqtt.CallbackAPIVersion.VERSION2).stat_sensors * get_size("idevices")  ### sensor count check
        common.check_for_no_registration(config)

    common.chirp_setup_and_run_test(caplog, run_test_codec_with_comment, test_params=dict(devices=1, codec=4), allowed_msg_level=logging.ERROR)
    i_sensor_err = 0
    for record in caplog.records:
        if record.msg == ERRMSG_CODEC_ERROR: i_sensor_err += 1
    assert i_sensor_err == 1
