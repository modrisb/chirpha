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
      battery:{
        data_event: "status",
        entity_conf: {
          value_template: "{{ value_json.batteryLevel | int }}",
          entity_category: "diagnostic",
          device_class: "battery",
          unit_of_measurement: "%",
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
