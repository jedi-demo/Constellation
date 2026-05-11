from .TTiInterface import TTiInterface
import re

class QL355TPII(TTiInterface):
    def __init__(self, ip_address: str):
        super().__init__(ip_address=ip_address)

    def initialize(self):
        self.connect()
        self._write("*CLS")

    def identify(self) -> str:
        return self._query("*IDN?")

    def set_output(self, channel: int, enable: bool):
        state = 1 if enable else 0
        self._write(f"OP{channel} {state}")

    def set_voltage(self, channel: int, voltage: float):
        self._write(f"V{channel} {voltage}")

    def set_current_limit(self, channel: int, current: float):
        self._write(f"I{channel} {current}")

    def set_ovp(self, channel: int, voltage: float):
        self._write(f"OVP{channel} {voltage}")

    def set_ocp(self, channel: int, current: float):
        self._write(f"OCP{channel} {current}")

    def _parse_value(self, text: str) -> float:
        match = re.search(r"[-+]?\d*\.\d+|\d+", text)
        if match:
            return float(match.group())
        return 0.0

    def get_voltage_readback(self, channel: int) -> float:
        ret = self._query(f"V{channel}O?")
        return self._parse_value(ret)

    def get_current_readback(self, channel: int) -> float:
        ret = self._query(f"I{channel}O?")
        return self._parse_value(ret)

    def get_limit_status(self, channel: int) -> int:
        try:
            ret = self._query(f"LSR{channel}?")
            return int(ret)
        except:
            return 0

    def get_execution_error(self) -> int:
        try:
            ret = self._query("EER?")
            return int(ret)
        except:
            return 0
