"""The Chirpstack LoRaWAN integration - setup."""
from __future__ import annotations
__version__ = "1.1.51"

import logging
import logging.handlers
import json
import signal
import os
import sys
from pathlib import Path
from typing import Final
import threading
import traceback

from .grpc import ChirpGrpc
from .mqtt import ChirpToHA
from .const import CONF_API_SERVER, CONF_API_PORT, CONF_MQTT_SERVER, CONF_MQTT_PORT, CONF_OPTIONS_LOG_LEVEL
from .const import CONF_APPLICATION_ID, DEFAULT_API_SERVER, DEFAULT_API_PORT, DEFAULT_MQTT_PORT, DEFAULT_MQTT_SERVER
from .const import CONF_MQTT_CHIRPSTACK_PREFIX, DEFAULT_MQTT_CHIRPSTACK_PREFIX

# https://stackoverflow.com/questions/2183233/how-to-add-a-custom-loglevel-to-pythons-logging-facility/13638084#13638084
DETAILED_LEVEL_NUM = 5
logging.addLevelName(DETAILED_LEVEL_NUM, "DETAIL")
def detail(self, message, *args, **kws):
    if self.isEnabledFor(DETAILED_LEVEL_NUM):
        self._log(DETAILED_LEVEL_NUM, message, args, **kws)
logging.Logger.detail = detail
# https://stackoverflow.com/questions/2183233/how-to-add-a-custom-loglevel-to-pythons-logging-facility/13638084#13638084

# Date/Time formats
FORMAT_DATE: Final = "%Y-%m-%d"
FORMAT_TIME: Final = "%H:%M:%S"
FORMAT_DATETIME: Final = f"{FORMAT_DATE} {FORMAT_TIME}"
#FMT = ( "%(asctime)s.%(msecs)03d chirpha %(levelname)s [%(name)s] %(message)s" )
FMT = ( "%(asctime)s.%(msecs)03d chirpha %(levelname)s %(message)s" )

CONFIGURATION_FILE = '/data/options.json'

_LOGGER = logging.getLogger(__name__)

INTERNAL_CONFIG = {
  CONF_API_SERVER: DEFAULT_API_SERVER,
  CONF_API_PORT: DEFAULT_API_PORT,
  CONF_MQTT_SERVER: DEFAULT_MQTT_SERVER,
  CONF_MQTT_PORT: DEFAULT_MQTT_PORT,
  CONF_MQTT_CHIRPSTACK_PREFIX: DEFAULT_MQTT_CHIRPSTACK_PREFIX,
}

class run_chirp_ha:
    def __init__(self, configuration_file) -> None:
        self._grpc_client = None
        self._mqtt_client = None
        self._config = None
        self._configuration_file = configuration_file
        signal.signal(signal.SIGTERM, self.stop_chirp_ha)
        threading.excepthook = self.subthread_failed

    def subthread_failed(self, args):
        _LOGGER.error("Chirp failed: %s : %s", args.exc_value, traceback.format_tb(args.exc_traceback))
        self.close_mqtt_loop()

    def stop_chirp_ha(self, signum, frame):
        _LOGGER.info("Shutdown requested")
        self.close_mqtt_loop()

    def close_mqtt_loop(self):
        if self._mqtt_client:   # close to exit server loop
            _LOGGER.info("Closing MQTT connection")
            self._mqtt_client.close()
            self._mqtt_client = None

    def main(self):
        logging.basicConfig(level=logging.INFO, format=FMT, datefmt=FORMAT_DATETIME)
        config = None
        try:
            module_dir = Path(globals().get("__file__", "./_")).absolute().parent
            with open(self._configuration_file, 'r') as file:
                config = json.load(file)
            config = INTERNAL_CONFIG | config
            self._config = config
            with open(str(module_dir)+'/classes.json', 'r') as file:
                classes = json.load(file)
            _LOGGER.info("ChirpHA started")
            try:
                logging.getLogger().setLevel(config[CONF_OPTIONS_LOG_LEVEL].upper())
            except Exception as error:
                _LOGGER.warning("Wrong log level specified '%s', assuming 'info'", config[CONF_OPTIONS_LOG_LEVEL])
                config[CONF_OPTIONS_LOG_LEVEL] = 'info'
            _LOGGER.debug("Logging level %s", config[CONF_OPTIONS_LOG_LEVEL].upper())
            _LOGGER.debug("Current directory %s, module directory %s", os.getcwd(), module_dir)
            _LOGGER.debug("Configuration file %s", self._configuration_file)
            _LOGGER.info("Version %s", __version__)
            self._grpc_client = ChirpGrpc(config, __version__)
            self._mqtt_client = ChirpToHA(config, __version__, classes, self._grpc_client)
            self._mqtt_client._client.loop_forever()
        except Exception as error:
            if logging.getLogger().getEffectiveLevel() == logging.DEBUG:
                _LOGGER.exception("Chirp failed: %s", str(error))
            else:
                _LOGGER.error("Chirp failed: %s", str(error))
        finally:
            if self._mqtt_client:
                _LOGGER.info("Closing MQTT connection")
                self._mqtt_client.close()
                self._mqtt_client = None
            if self._grpc_client:
                _LOGGER.info("Closing gRPC connection")
                self._grpc_client.close()
                self._grpc_client = None


if __name__=='__main__':
    run_chirp_ha(sys.argv[1] if len(sys.argv)>1 else CONFIGURATION_FILE).main()
    _LOGGER.info("Done.")
