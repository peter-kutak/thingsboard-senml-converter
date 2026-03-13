from typing import Any, Tuple
from simplejson import loads

from thingsboard_gateway.connectors.converter import Converter
from thingsboard_gateway.gateway.constants import REPORT_STRATEGY_PARAMETER, TELEMETRY_PARAMETER, TIMESERIES_PARAMETER
from thingsboard_gateway.gateway.entities.converted_data import ConvertedData
from thingsboard_gateway.gateway.entities.datapoint_key import DatapointKey
from thingsboard_gateway.gateway.entities.report_strategy_config import ReportStrategyConfig
from thingsboard_gateway.gateway.entities.telemetry_entry import TelemetryEntry
from thingsboard_gateway.tb_utility.tb_utility import TBUtility


class SenMLConverter(Converter):
    """
    Uplink converter is used to convert incoming data to the format that platform expects.
    Such as we create uplink converter for each configured device,
    this converter is used to convert incoming data from only one device.
    Because config, that we passed to init method, is device specific.
    If your connector can handle multiple devices, you can create one converter for all devices.
    """

    def __init__(self, config, logger):
        self._log = logger
        self.__config = config
        self.__device_report_strategy = None
        self.__device_name = self.__config.get('deviceName', self.__config.get('name', 'SenMLDevice'))
        self.__device_type = self.__config.get('deviceType', self.__config.get('type', 'default'))
        try:
            self.__device_report_strategy = ReportStrategyConfig(self.__config.get(REPORT_STRATEGY_PARAMETER))
        except ValueError as e:
            self._log.trace("Report strategy config is not specified for device %s: %s", self.__device_name, e)

    def convert(self, config, data: bytes):
        """Converts incoming data to the format that platform expects. Config is specified only for RPC responses."""
        self._log.debug("---------------------------------");
        self._log.debug("config: %s is nn %s", config, (config is not None));
        self._log.debug("__config: %s", self.__config);
        self._log.debug("Data to convert: %s", data)
        if config is not None:
            converted_data = self.parse_senml(self._log, data, config, self.__device_report_strategy)
            self._log.debug("converted Data: %s", converted_data)
            return converted_data
        else:
            return


    """
    Converter pre SenML (RFC 8428) formát
    """
    
    from datetime import datetime
    @staticmethod
    def parse_senml(log, payload, topic, device_report_strategy):
        """
        Parsuje SenML JSON a konvertuje na ThingsBoard formát
        """
        try:
            # Parsuj SenML
            if isinstance(payload, str):
                senml_data = loads(payload)
            else:
                senml_data = payload
            
            # Ak je to pole, spracuj ako pole SenML záznamov
            if not isinstance(senml_data, list):
                senml_data = [senml_data]
            
            # Extrahovanie base properties
            base_name = ""
            base_time = None
            base_unit = ""
            base_version = 1
            
            # Zbieraj telemetry a attributes
            telemetry = {}
            attributes = {}
            device_name = "UnknownDevice"
            
            for record in senml_data:
                # Base properties (bn, bt, bu, bv)
                if "bn" in record:
                    base_name = record["bn"]
                    # Extrahovanie device mena z bn
                    #if "/" in base_name:
                    #    device_name = base_name.split("/")[-1]
                    #else:
                    #    device_name = base_name
                    device_name = base_name.replace("/", "")
                
                if "bt" in record:
                    base_time = int(record["bt"] * 1000)  # Konvertuj na ms
                
                if "bu" in record:
                    base_unit = record["bu"]
                
                if "bv" in record:
                    base_version = record["bv"]
                
                # Zbieraj dáta
                if "n" in record:  # name - povinné
                    key = record["n"]
                    
                    # Value (v) - telemetry
                    if "v" in record:
                        telemetry[key] = record["v"]
                    
                    # String value (vs)
                    elif "vs" in record:
                        telemetry[key] = record["vs"]
                    
                    # Boolean value (vb)
                    elif "vb" in record:
                        telemetry[key] = record["vb"]
                    
                    # Data value (vd) - base64
                    elif "vd" in record:
                        telemetry[key] = record["vd"]
            
            # Ak nie je timestamp, použi aktuálny
            if base_time is None:
                base_time = int(datetime.now().timestamp() * 1000)
            
            # Vytvor ThingsBoard formát
            result = ConvertedData(device_name = device_name, device_type="default")
            for k,v in telemetry.items():
                log.debug(f"key: {k}")
                log.debug(f"val: {v}")
                datapoint_key = TBUtility.convert_key_to_datapoint_key(k, device_report_strategy, {})
                telemetry_entry = TelemetryEntry({datapoint_key: v}, ts=base_time)
                result.add_to_telemetry(telemetry_entry) 
            
            log.info(f"SenML parsovaný: {device_name}")
            return result
            
        except Exception as e:
            log.error(f"Chyba pri parsovaní SenML: {e}")
            return None

