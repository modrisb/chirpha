function getHaDeviceInfo() {
  return {
    device: {
      manufacturer: "Dragino Technology Co., Limited",
      model: "LDS02",
    },
    entities: {
      door:{
        entity_conf: {
          value_template: "{{ value_json.object.DOOR_OPEN_STATUS | int }}",
          device_class: "door",
          payload_on: 1,
          payload_off: 0
        }
      },
      open_times:{
        integration: "sensor",
        entity_conf: {
          value_template: "{{ value_json.object.DOOR_OPEN_TIMES | int }}",
          device_class: "volume",
          //enabled_by_default:false,
        }
      },
      open_duration:{
        entity_conf: {
          value_template: "{{ value_json.object.LAST_DOOR_OPEN_DURATION | int }}",
          device_class: "duration",
          unit_of_measurement: "min",
          //enabled_by_default:false,
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
      battery_voltage:{
        entity_conf: {
          value_template: "{{ value_json.object.BAT_V | float }}",
          entity_category: "diagnostic",
          device_class: "voltage",
          unit_of_measurement: "V",
        }
      },
      clear_counting:{
        integration: "button",
        entity_conf: {
          command_topic: "{command_topic}",
          payload_press: '{"devEui":"{dev_eui}","fPort":1,"data":"pgE="}'
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
