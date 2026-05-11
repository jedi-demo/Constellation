from abc import ABCMeta, abstractmethod
import socket
import time
from threading import Lock

class TTiInterface(metaclass=ABCMeta):
    def __init__(self, ip_address: str, timeout: float = 5.0):
        self._ip = ip_address
        self._port = 9221
        self._timeout = timeout
        self._socket = None
        self._lock = Lock()

    def connect(self):
        with self._lock:
            if self._socket is None:
                try:
                    self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self._socket.settimeout(self._timeout)
                    self._socket.connect((self._ip, self._port))
                except Exception as e:
                    self._socket = None
                    print(f"Socket Connection Error {self._ip}:{self._port} -> {e}")
                    raise

    def close(self):
        with self._lock:
            if self._socket:
                try:
                    self._socket.close()
                except:
                    pass
                self._socket = None

    def _write(self, command: str):
        if not self._socket: self.connect()
        
        with self._lock:
            try:
                msg = f"{command}\n".encode('ascii')
                self._socket.sendall(msg)
                time.sleep(0.05)
            except (BrokenPipeError, ConnectionResetError, socket.error):
                self.close()
                self.connect()
                self._socket.sendall(f"{command}\n".encode('ascii'))

    def _query(self, command: str) -> str:
        if not self._socket: self.connect()
        
        with self._lock:
            try:
                # Send
                self._socket.sendall(f"{command}\n".encode('ascii'))
                
                # Wait for device processing
                time.sleep(0.3)

                # Read
                response = self._socket.recv(1024)
                return response.decode('ascii').strip()
                
            except (BrokenPipeError, ConnectionResetError, socket.error) as e:
                print(f"Socket lost: {e}. Reconnecting...")
                self.close()
                self.connect()
                
                # Retry
                self._socket.sendall(f"{command}\n".encode('ascii'))
                time.sleep(0.3)
                return self._socket.recv(1024).decode('ascii').strip()

    @abstractmethod
    def identify(self) -> str: pass
    @abstractmethod
    def initialize(self): pass
    @abstractmethod
    def set_output(self, channel: int, enable: bool): pass
    @abstractmethod
    def set_voltage(self, channel: int, voltage: float): pass
    @abstractmethod
    def set_current_limit(self, channel: int, current: float): pass
    @abstractmethod
    def set_ovp(self, channel: int, voltage: float): pass
    @abstractmethod
    def set_ocp(self, channel: int, current: float): pass
    @abstractmethod
    def get_voltage_readback(self, channel: int) -> float: pass
    @abstractmethod
    def get_current_readback(self, channel: int) -> float: pass
    @abstractmethod
    def get_limit_status(self, channel: int) -> int: pass
    @abstractmethod
    def get_execution_error(self) -> int: pass
