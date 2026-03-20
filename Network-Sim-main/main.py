from core import Frame, Device, Hub
from phy_layer import PhysicalLayer

# Devices
A = Device("A")
B = Device("B")
C = Device("C")

# Hub
hub = Hub("Hub1")

# Connections (IMPORTANT)
A.connect(hub)
B.connect(hub)
C.connect(hub)

# Frame (broadcast address)
frame = Frame(A.mac_address, "FF:FF", "Hello Everyone")

# Physical layer
phy = PhysicalLayer()

# Broadcast via hub
hub.broadcast(A, frame, phy)''