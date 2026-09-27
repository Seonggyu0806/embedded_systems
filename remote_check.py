import platform
import socket
from pathlib import Path

print("host:", socket.gethostname())
print("os:", platform.system())
print("cpu:", platform.machine())
print("file:", Path(__file__).resolve())
