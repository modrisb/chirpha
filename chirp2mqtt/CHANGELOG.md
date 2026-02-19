<!-- https://developers.home-assistant.io/docs/add-ons/presentation#keeping-a-changelog -->

## 1.1.150

- default_entity_id naming fix - added leading integration
- fixed auto generation for HA integration function getHaDeviceInfo and corresponding test cases

## 1.1.149

- Upgrade to ghcr.io/hassio-addons/base:20.0.1, CHIRPSTACK_VERSION: 4.16.1, CHIRPSTACK_GATEWAY_BRIDGE_VERSION: 4.1.1
- Added auto generation for HA integration function getHaDeviceInfo with minimal configuration if it is absent in device profile javascript codec
- Replaced depricated object_id with default_entity_id in entity configuration

## 1.1.148

- Upgrade to ghcr.io/hassio-addons/base:18.1.1, CHIRPSTACK_VERSION: 4.14.1

## 1.1.147

- Fixed issue with event/frame appearance in ingress

## 1.1.146

- Fixed value processing for cases when not(value)==True

## 1.1.144

- Ingress support added

## 1.1.143

- Synchronized code with https://github.com/modrisb/chirp
- Upgrade to ghcr.io/hassio-addons/base:18.0.3, CHIRPSTACK_VERSION: 4.13.0

## 1.1.142

- Fixed issue with enabled_by_default processing

## 1.1.141

- Fixed database re-creation on every add-on re-start

## 1.1.140

- Upgrade to CHIRPSTACK_VERSION: 4.12.1

## 1.1.139

- Test code synchronization/refactoring

## 1.1.138

- DOCS.md updates: template importing and sensor naming details, added codec example for Makerfabs Agrosense AGLWPP01
- Upgrade to ghcr.io/hassio-addons/base:17.2.4

## 1.1.137

- Upgrade to ghcr.io/hassio-addons/base:17.2.1, CHIRPSTACK_VERSION: 4.11.1

## 1.1.136

- Code synchronization with chirp integration .
- Log level reduced to warnings for ChirpStack gateway .

## 1.1.135

- Added device eui specific parameter support via getHaDeviceInfo .

## 1.1.134

- Added option to import device templates from git repository.

## 1.1.132

- HA MQTT integration component device name processing change - getHaDeviceInfo data now has highest priority, the same for entities and 'enabled_by_default'.

## 1.1.131

- ChirpStack secret to configuration parameters
- HA MQTT integration component name processing change - getHaDeviceInfo data now has highest priority

## 1.1.128

- Added LORA region selection to configuratiom, fixed missinging MQTT user/password propagation to ChirpStack components (defaults were used always)

## 1.1.127

- Added optional expire after MQTT configuration item discovery message

## 1.1.126

- Added logging control via MQTT message: topic application/{ChirpStack appId}/bridge/info, message '{"log_level":"debug"}'. Added per device online checks. Initialization and logging re-factoring

## 1.1.125

- Tests extension and minor fixes in code, file cleanup. Initialization re-factoring, fixed issue with log level

## 1.1.116

- Code extended to support MQTT component integrations. Replaced custom js evaluator with dukpy package

## 1.1.108

- Added MQTT server naming requirements to documentation. Added payload checks. Fixed MQTT server IP naming in region description file. Upgrade to ghcr.io/hassio-addons/base:17.1.0, CHIRPSTACK_VERSION: 4.11.0

## 1.1.102

- Initial release
