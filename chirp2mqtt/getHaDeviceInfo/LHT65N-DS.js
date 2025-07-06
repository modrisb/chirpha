function getHaDeviceInfo() {
  return {
    device: {
      manufacturer: "Dragino Technology Co., Limited",
      model: "LHT65N-DS",
    },
    entities: {
      humidity:{
        entity_conf: {
          value_template: "{{ value_json.object.Hum_SHT | float }}",
          device_class: "humidity",
          unit_of_measurement: "%"
        }
      },
      temperature:{
        entity_conf: {
          value_template: "{{ value_json.object.TempC_SHT | float }}",
          device_class: "temperature",
          unit_of_measurement: "°C"
        }
      },
      door:{
        entity_conf: {
          value_template: "{{ value_json.object.Exti_pin_level }}",
          device_class: "door",
          payload_on: "Low",
          payload_off: "High"
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
