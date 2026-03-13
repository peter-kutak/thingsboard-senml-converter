Developed for ThingsBoard 4.3 

ThingsBoard gateway was installed from deb package as standalone service (not docker-toto je original riesenie ale ja nemam doker)

copy senml_converter.py into <pre>/var/lib/thingsboard_gateway/extensions/mqtt/</pre>
and restart <pre>service systemctl restart thingsboard-gateway</pre>

WebUI

- login as sysadmin and create Tenant

- login as tenant administrator and configure gateway

LeftMenu-Entities -> Gateways -> (+) Add gateway -> mygateway/default -> [ Create ] -> Connectors configuration -> (+) Add -> MQTT/myconnector/INFO -> [Add] -> click on myconnector -> Tab connection to broker -> Fill all info about mqtt broker providing our SenML data -> Tab Data mapping -> (+) Add -> Topic: myhome -> QoS: 1 -> Payload type: Custom -> Extension: SenMLConverter -> [Add] -> [Save]

after data receive and parse new devices will automaticaly pop-up in LeftMenu-Entities -> Devices -> Click on some device and received values will be on tab Latest Telemetry

(WebUI sometimes does not redraws correctly)
