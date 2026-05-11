import time
from typing import Any

from constellation.core.configuration import Configuration
from constellation.core.satellite import Satellite
from constellation.core.commandmanager import cscp_requestable
from constellation.core.fsm import SatelliteState
from constellation.core.message.cscp1 import CSCP1Message
from constellation.core.monitoring import schedule_metric

from .QL355TPII import QL355TPII

sampling_interval = 2.0 

class TTiQLSatellite(Satellite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.device = None
        self.ip = None

    def do_initializing(self, config: Configuration) -> str:
        self.ip = config["ip"]
        
        self.v1 = config["voltage1"] # 0
        self.i1 = config["current_limit1"] # 1
        self.ovp1 = config["ovp1"] # 40.0
        self.ocp1 = config["ocp1"] # 5.5

        self.v2 = config["voltage2"] # 0
        self.i2 = config["current_limit2"] # 1
        self.ovp2 = config["ovp2"] # 40 
        self.ocp2 = config["ocp2"] # 5.5

        try:
            self.device = QL355TPII(self.ip)
            self.device.initialize()
            idn = self.device.identify()
            self.log.info(f"Connected to TTi: {idn}")
        except Exception as e:
            raise RuntimeError(f"Connection failed to {self.ip}: {e}")

        #self.reset_scheduled_metrics()
        
        return f"Initialized at {self.ip}"

    @schedule_metric("V", sampling_interval)
    def CH1_V(self):
        if self.device: return self.device.get_voltage_readback(1)
        return 0.0
   
    @schedule_metric("A", sampling_interval)
    def CH1_I(self):
        if self.device: return self.device.get_current_readback(1)
        return 0.0
   
    @schedule_metric("bitmask", sampling_interval)
    def CH1_STAT(self):
        if self.device: return self.device.get_limit_status(1)
        return 0
   
    @schedule_metric("V", sampling_interval)
    def CH2_V(self):
        if self.device: return self.device.get_voltage_readback(2)
        return 0.0
   
    @schedule_metric("A", sampling_interval)
    def CH2_I(self):
        if self.device: return self.device.get_current_readback(2)
        return 0.0
   
    @schedule_metric("bitmask", sampling_interval) 
    def CH2_STAT(self):
        if self.device: return self.device.get_limit_status(2)
        return 0

    @schedule_metric("code", sampling_interval)
    def LAST_ERROR(self):
        if self.device:
            err = self.device.get_execution_error()
            if err != 0:
                self.log.warning(f"Device Error Code: {err}")
            return err
        return 0

    @cscp_requestable
    def set_live_voltage(self, request: CSCP1Message) -> tuple[str, Any, dict]:
        data = request.payload
        channel = 1
        voltage = 0.0

        if isinstance(data, (int, float)):
            voltage = float(data)
        elif isinstance(data, dict):
            channel = data.get("ch", 1)
            voltage = float(data.get("v", 0.0))
        
        if self.device:
            self.device.set_voltage(channel, voltage)
            self.log.info(f"Live Voltage CH{channel} -> {voltage} V")
            return f"CH{channel} set to {voltage}V", voltage, {}
        else:
            return "Error: Device not connected", None, {}

    @cscp_requestable
    def set_live_current(self, request: CSCP1Message) -> tuple[str, Any, dict]:
        data = request.payload
        channel = 1
        current = 0.0

        if isinstance(data, (int, float)):
            current = float(data)
        elif isinstance(data, dict):
            channel = data.get("ch", 1)
            current = float(data.get("i", 0.0))

        if self.device:
            self.device.set_current_limit(channel, current)
            self.log.info(f"Live Current CH{channel} -> {current} A")
            return f"CH{channel} limit set to {current}A", current, {}
        return "Error", None, {}

    @cscp_requestable
    def set_output_state(self, request: CSCP1Message) -> tuple[str, Any, dict]:
        data = request.payload
        channel = 1
        state = False
        
        if isinstance(data, bool) or isinstance(data, int):
            state = bool(data)
        elif isinstance(data, dict):
            channel = data.get("ch", 1)
            state = bool(data.get("on", False))

        if self.device:
            self.device.set_output(channel, state)
            s_str = "ON" if state else "OFF"
            self.log.info(f"Output CH{channel} -> {s_str}")
            return f"CH{channel} is {s_str}", state, {}
        return "Error", None, {}

    def do_launching(self) -> str:
        self.device.set_ovp(1, self.ovp1); self.device.set_ocp(1, self.ocp1)
        self.device.set_voltage(1, self.v1); self.device.set_current_limit(1, self.i1)
        
        self.device.set_ovp(2, self.ovp2); self.device.set_ocp(2, self.ocp2)
        self.device.set_voltage(2, self.v2); self.device.set_current_limit(2, self.i2)

        self.device.set_output(1, True)
        self.device.set_output(2, True)
        return "Channels 1 & 2 ON"
    
    def do_landing(self) -> str:
        if self.device:
            self.device.set_output(1, False)
            self.device.set_output(2, False)
        return "Channels 1 & 2 OFF"
    
    def reentry(self) -> None:
        if self.device: self.device.close()
        super().reentry()

    def do_reconfigure(self, partial_config: Configuration) -> str:
        if "voltage1" in partial_config:
            self.v1 = partial_config["voltage1"]
            self.device.set_voltage(1, self.v1)
        if "current_limit1" in partial_config:
            self.i1 = partial_config["current_limit1"]
            self.device.set_current_limit(1, self.i1)
        if "voltage2" in partial_config:
            self.v2 = partial_config["voltage2"]
            self.device.set_voltage(2, self.v2)
        if "current_limit2" in partial_config:
            self.i2 = partial_config["current_limit2"]
            self.device.set_current_limit(2, self.i2)
        return "Reconfigured"
