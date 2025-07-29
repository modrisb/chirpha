# Home Assistant Add-on: Chirp2MQTT middleware

## Installation

Follow these steps to get the add-on installed on your system:

1. Navigate in your Home Assistant frontend to **Settings** -> **Add-ons** -> **Add-on store**.
2. Add https://github.com/modrisb/chirpha to repository list.
3. Find the "Chirp2MQTT" add-on and click it.
4. Click on the "INSTALL" button.

## How to use

Chirp2MQTT middleware add-on integrates ChirpStack server, Redis, PostgreSQL and small Python management component into single unit that could be installed on Home Assistant managed system with Mosquitto MQTT broker available at IP address core-mosquitto. Add-on allows to integrate LoRaWAN devices into HA system via MQTT integration. Python management component registers all known and enabled in ChirpStack LoRaWAN devices within MQTT, handles battery level set-up at service start, restores known sensor values and synchronize device list upon request. Device registration is handled via ChirpStack WWW interface and this may include updates in device Codec javascript code.
Before add-on is installed you need to create Mosquitto MQTT broker user/password (remember that `homeassistant` or `addons` user names are reserved) with authority to subscribe/publish any topic. Recent version uses plain MQTT connection without any certificates on default port 1883.

The add-on need to be configured before started, see **Configuration** section for details. Start add-on, initial start-up requires more time that successive startups. There is option to restore ChirpStack PostgreSQL database from backup file in HA /share/chirp2mqtt/chirp_db, on success backup file is renamed to chirp_db.restored .

"Chirp2MQTT Bridge" device should show up as parent for all other LoRaWAN devices managed by ChirpStack server. Bridge device exposes 'Reload devices' control to synchronize device list with server. Child devices are listed under "Connected devices". Child names are retrieved from ChirpStack server and must be managed from here. Integration uses LoRa deveui to identify device internally.

Add-on on start-up searches for specific configuration files in HA directories /share/chirp2mqtt/etc/chirpstack and /share/chirp2mqtt/etc/chirpstack-gateway-bridge and replaces default configuration files with those customized. Default ChirpStack configuration files assumes on Semtech interface on port 1700.
Python management component ensures that ChirpStack have at least 1 tenant and 1 application in its database by creating missing objects.

## Configuration

Add-on default configuration in yaml format:

```yaml
application_id: 72a56954-700f-4a52-90d2-86cf76df5c57
mqtt_user: loramqtt
mqtt_password: ploramqtt
discovery_prefix: homeassistant
options_start_delay: 2
options_restore_age: 4
options_online_per_device: 0
options_log_level: info
database_actions: None
import_actions: https://github.com/brocaar/lorawan-devices
lora_region: eu868
chirpstack_secret: you-must-replace-this
```

### Option: `application_id` (optional)

ChirpStack application id that hosts LoRaWAN devices.

Default value: 1st tenant's 1st application id. Default value is used also in case if application_id does not exist.

#### Option: `mqtt_user` (required)

Set to created MQTT user id.

#### Option: `mqtt_password` (optional)

Set to created MQTT user password.

### Option: `discovery_prefix` (optional)

HA MQTT integration discovery prefix.

Default value: 'homeassistant'.

### Option: `options_start_delay` (optional)

Delay in seconds between device registration in HA MQTT integration and it's usage start.

Default value: 2 .

### Option: `options_restore_age` (optional)

Time period in seconds to wait for device to show up for sensor value restoration.

Default value: 4 .

### Option: `options_log_level`

Python management application log level, one of 'critical', 'fatal', 'critical', 'error', 'warning', 'info', 'debug', 'detail' .

Default value: 'info' .

### Option: `options_online_per_device`

Time period in minutes used for device online checks. 0 value disables online checks and device is considered online all the time.

Default value: 0 .

### Option: `options_add_expire_after`

Switch to enable expire after setting for MQTT, time value is taken from device profile uplink interval. 'expire_after' still could be set in getHaDeviceInfo and using value {None} removes setting from discovery message.

Default value: false/off .

### Option: `database_actions`

ChirpStack database actions, one of 'None', 'Backup', 'Restore', 'Backup and restore' . 'Backup' - add-on takes database backup and stores it in /share/chirp2mqtt/chirp_db file and freeze execution. 'Restore' - restores database from /share/chirp2mqtt/chirp_db, renames backup file to chirp_db.restored and add-on continues service. 'Backup and restore' combines both 'Backup' and 'Restore': firstly applied creates backup file and stops; on second add-on start restores database and continues service. Last option might be handy to switch between add-on builds with different versions of Postgresql.

Default value: 'None' .

### Option: `import_actions`

URL to git repository with LoRaWAN device templates or 'none'. Repository is imported before ChirsStack starts. Parameter must be reset after importing to 'none', otherwise import will be started again on next add-on start-up. Chirp2MQTT automatically imports repository from HA directory /share/chirp2mqtt/lorawan-devices and marks import by creating file 'imported' to prevent continuous imports.

Default(initial) value: 'https://github.com/brocaar/lorawan-devices' .

### Option: `lora_region`

Selects Lora region for ChirpSatck run.

Default value: EU868 .

### Option: `chirpstack_secret`

Sets security string for ChirpStack operations.

Default value: you-must-replace-this .


## Support

[Chirpstack](https://chirpstack.io)

[Home Assistant](https://www.home-assistant.io)

[Chirp2mqtt](https://github.com/modrisb/chirpha)

## Supported devices
Home Assistant will [automatically discover](https://www.home-assistant.io/integrations/mqtt/#mqtt-discovery) devices and set the right entity information for supported devices. For this to work, modify the codec in the device profile with one of the [examples](https://github.com/modrisb/chirpha/tree/main/chirp2mqtt/getHaDeviceInfo).
To modify or add new devices to the examples, see how to update codecs below.


## Codec updates

Regular ChirpStack codec contains entries supporting payload decoding/encoding. Codec must be appended by function similar to:

```
function getHaDeviceInfo() {
  return {
    device: {
      manufacturer: "Milesight IoT Co., Ltd",
      model: "WS52x"
    },
    entities: {
        current:{
        entity_conf: {
          value_template: "{{ (value_json.object.current | float) / 1000 }}",
          entity_category: "diagnostic",
          state_class: "measurement",
          device_class: "current",
          unit_of_measurement: "A"
        }
      },
        factor:{
        entity_conf: {
          value_template: "{{ (value_json.object.factor | float) / 100 }}",
          entity_category: "diagnostic",
          state_class: "measurement",
          device_class: "power_factor",
        }
      },
      power:{
        entity_conf: {
          value_template: "{{ value_json.object.power | float }}",
          entity_category: "diagnostic",
          state_class: "measurement",
          device_class: "power",
          unit_of_measurement: "W"
        }
      },
      voltage:{
        entity_conf: {
          value_template: "{{ value_json.object.voltage | float }}",
          entity_category: "diagnostic",
          state_class: "measurement",
          device_class: "voltage",
          unit_of_measurement: "V"
        }
      },
      outage:{
        integration: "binary_sensor",
        entity_conf: {
          entity_category: "diagnostic",
          device_class: "power"
        }
      },
      power_sum:{
        entity_conf: {
          value_template: "{{ (value_json.object.power_sum | float) / 1000 }}",
          state_class: "total_increasing",
          device_class: "energy",
          unit_of_measurement: "kWh"
        }
      },
      state:{
       integration: "switch",
       entity_conf: {
          value_template: "{{ value_json.object.state }}",
          command_topic: "{command_topic}",
          state_on: "open",
          state_off: "close",
          payload_off: '{{"dev_eui":"{dev_eui}","confirmed":true,"fPort":85,"data":"CAAA/w=="}}',
          payload_on: '{{"dev_eui":"{dev_eui}","confirmed":true,"fPort":85,"data":"CAEA/w=="}}'
        }
      },
      rssi:{
        entity_conf: {
          value_template: "{{ value_json.rxInfo[-1].rssi | int }}",
          entity_category: "diagnostic",
          device_class: "signal_strength",
          unit_of_measurement: "dBm",
        }
      }
    }
  };
}
```
This function returns structure that describes device and its entities in terms of Home Assistant. Substructure device: {} describes HA MQTT device and is applied to all substructures under entities: {}.
Device description contains manufacturer and model information that is used only as reference. Add-on adds
- device name as in ChirpStack
- identifier based on deveui to join all entities (sensors) together into device
- via_device field to show bridge device as parent .
Entities (sensors) structure contains
- entity name; name must match one used in decode function that is defined above and is supplied by device vendor; this name will be replaced with one set in ChirpStack's device profile measurements;
- integration and entity_conf is defined on the next level of structure;
- integration sets MQTT component integration name, this could be name of one of MQTT components, default is "sensor"; if device class is set in it may allow to automatically select integration;
- entity_conf defines fields that control device sensor appearance in MQTT integration; value_template describes how to extract sensor value from payload, default is value_template: "{{ value_json.entity_name }}". Usually value need to be converted to specific type (int, float).  On both device and entity levels substructure named 'dev_eui' followed by device's real eui with device specific settings for device/entity. All such substructures are deleted from final configuration message, but substructure elements are pushed level up if dev_eui matches.

There are 4 special values in description structure returned by getHaDeviceInfo: "{None}", "{status_topic}", "{command_topic}", "{"dev_eui"}". Keys with value "{None}" are deleted during processing; "{status_topic}" replaced with ChirpStack's status topic name; "{command_topic}" replaced with ChirpStack's command topic name. Values with "{"dev_eui"}" are formatted to current dev_eui. There are several examples of getHaDeviceInfo for various devices in sub-directory 'getHaDeviceInfo'.
