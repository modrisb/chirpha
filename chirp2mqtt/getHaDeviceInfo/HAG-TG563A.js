  function getHaDeviceInfo() {
    return {
      device: {
        manufacturer: "Hager Group",
        model: "TG563A Smoke Detector",
      },
      entities: {
        temperature:{
          entity_conf: {
            value_template: "{{ value_json.object.temperature | float }}",
            device_class: "temperature",
            unit_of_measurement: "°C"
          }
        },
        minimumTemperature:{
          entity_conf: {
            value_template: "{{ value_json.object.minimumTemperature | float }}",
            device_class: "temperature",
            unit_of_measurement: "°C"
          }
        },
        maximumTemperature:{
          entity_conf: {
            value_template: "{{ value_json.object.maximumTemperature | float }}",
            device_class: "temperature",
            unit_of_measurement: "°C"
          }
        },
        batteryLevel:{
          entity_conf: {
            value_template: "{{ value_json.object.batteryLevel | float }}",
            device_class: "voltage",
            entity_category: "diagnostic",
            unit_of_measurement: "V"
          }
        },
        energyUsage:{
          integration: "sensor",
          entity_conf: {
            value_template: "{{ value_json.object.energyUsage | int }}",
            entity_category: "diagnostic",
            //device_class: "energy",
            unit_of_measurement: "%"
          }
        },
        distanceThreshold:{
          entity_conf: {
            entity_category: "diagnostic",
            value_template: "{{ value_json.object.distanceThreshold | int }}",
            device_class: "distance",
            unit_of_measurement: "cm"
          }
        },
        smoke:{
          integration: "binary_sensor",
          entity_conf: {
            value_template: "{{ value_json.object.status.smokeAlarm | int }}",
            device_class: "smoke",
            payload_on: 1,
            payload_off: 0
          }
        },
        smokeAlarmTimeCounter:{
          entity_conf: {
            value_template: "{{ value_json.object.smokeAlarmTimeCounter | int }}",
            device_class: "duration",
            unit_of_measurement: "min",
          }
        },
        smokeAlarmCounter:{
          entity_conf: {
            value_template: "{{ value_json.object.smokeAlarmCounter | int }}",
            device_class: "volume",
          }
        },
        battery:{
          integration: "binary_sensor",
          entity_conf: {
            value_template: "{{ value_json.object.status.batteryLow | int }}",
            entity_category: "diagnostic",
            device_class: "battery",
            payload_on: 1,
            payload_off: 0
          }
        },
        battery:{
          data_event: "status",
          entity_conf: {
            value_template: "{{ value_json.batteryLevel | int }}",
            entity_category: "diagnostic",
            device_class: "battery",
            unit_of_measurement: "%",
          }
        },
      transmissionPeriod:{
          integration: "select",
          entity_conf: {
              value_template: "{{ (value_json.object.configuration.transmissionPeriod | int | string )+  ' h' }}",
              command_topic: "{command_topic}",
              command_template: '{"devEui":"{dev_eui}","fPort":1,"object":{ "command": "SET_TX_PERIOD", "parameter": {{ this.attributes.options.index(value) }} } }',
              options:[ "1 h", "2 h", "4 h", "6 h", "8 h", "12 h", "24 h",  "48 h" ] ,
            }
        },
        additionalDataEnabled:{
          integration: "switch",
          entity_conf: {
            value_template: "{{ value_json.object.configuration.additionalDataEnabled | int }}",
            command_topic: "{command_topic}",
            state_on: 1,
            state_off: 0,
            //payload_off: '{"devEui":"{dev_eui}","fPort":1,"data":"EA=="}',
            payload_on: '{"devEui":"{dev_eui}","fPort":1,"data":"EQ=="}'
          }
        },
        obstructionEventEnabled:{
          integration: "switch",
          entity_conf: {
            value_template: "{{ value_json.object.configuration.obstructionEventEnabled | int }}",
            command_topic: "{command_topic}",
            state_on: 1,
            state_off: 0,
            //payload_off: '{"devEui":"{dev_eui}","fPort":1,"data":"QA=="}',
            payload_on: '{"devEui":"{dev_eui}","fPort":1,"data":"QQ=="}'
          }
        },
        smokeEventEnabled:{
          integration: "switch",
          entity_conf: {
            value_template: "{{ value_json.object.configuration.smokeEventEnabled | int }}",
            command_topic: "{command_topic}",
            state_on: 1,
            state_off: 0,
            //payload_off: '{"devEui":"{dev_eui}","fPort":1,"data":"UA=="}',
            payload_on: '{"devEui":"{dev_eui}","fPort":1,"data":"UQ=="}'
          }
        },
        SEND_ADDITIONAL_DATA_IN_NEXT_UPLINK:{
          integration: "button",
          entity_conf: {
            command_topic: "{command_topic}",
            payload_press: '{"devEui":"{dev_eui}","fPort":1,"data":"gA=="}'
          }
        },
        resetSmokeEvent:{
          integration: "button",
          entity_conf: {
            command_topic: "{command_topic}",
            payload_press: '{"devEui":"{dev_eui}","fPort":1,"data":"UA=="}'
          }
        },
        rssi:{
          entity_conf: {
            value_template: "{{ value_json.rxInfo[-1].rssi | int }}",
            entity_category: "diagnostic",
            device_class: "signal_strength",
            unit_of_measurement: "dBm",
          }
        },
        snr:{
          integration: "sensor",
          entity_conf: {
            value_template: "{{ value_json.rxInfo[-1].snr | int }}",
            entity_category: "diagnostic",
            unit_of_measurement: "dB",
          }
        }
      }
    };
  }
