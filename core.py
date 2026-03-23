import uuid

class Frame:
    """The universal data object shared by all layers."""
    def __init__(self, source_mac, dest_mac, data, error_bit=0):
        self.source_mac = source_mac
        self.dest_mac = dest_mac
        self.payload = data

        self.error_code = None      # Could be CRC or Checksum 
        self.seq_num = 0            # For Sliding Window
        self.is_ack = False         # For Flow Control acknowledgments

        self.preamble = "10101010"    # For the Physical Layer teammate

# Create hub and end_device/switch class that inherits from this... for physical/data link layer
class Device:
    def __init__(self, name):
        self.name = name # Readable names like A, B, switch1
        self.mac_address = hex(uuid.uuid4().int)[:12] # Simple unique MAC
        self.ports = [] # Connections to other devices

    def connect(self, other_device):
        """Creates a physical connection between two devices [cite: 10]"""
        if other_device not in self.ports:
            self.ports.append(other_device)
            other_device.ports.append(self)
            print(f"Connected {self.name} <---> {other_device.name}")

class SimulatorCore:
    def __init__(self):
        self.all_devices = {}

    def add_device(self, device_obj):
        self.all_devices[device_obj.name] = device_obj

    def get_stats(self):
        """
        Logic for Submission 1: Report domains.
        - Hubs share a collision domain.
        - Switches break collision domains but share a broadcast domain.
        """
        # This is a simplified logic for your report
        collision_domains = 0
        broadcast_domains = 1 # Simplified for local network
        
        for name, dev in self.all_devices.items():
            if "Switch" in name:
                collision_domains += len(dev.ports)
            if "Hub" in name:
                collision_domains += 1
        
        print(f"\n--- Network Report ---")
        print(f"Collision Domains: {collision_domains}")
        print(f"Broadcast Domains: {broadcast_domains}")


class Hub(Device): # hub is a netowrking device which inherits from Devices 
    def __init__(self, name):
        super().__init__(name) #parent class constructor 

    def broadcast(self, sender, frame, datalink_layer): # hub broadcast data to all devices
        print(f"\n[Hub] Broadcasting data from {sender.name}...")

        for device in self.ports: # loop for every device which is connected to hub
            if device != sender: # sends data to all except sender
                datalink_layer.physical_layer.transmit(sender, device, frame) # data transmit through phy layer


class Switch(Device):
    def __init__(self, name):
        super().__init__(name)
        self.mac_table = {}  # MAC Address (string) -> Device Object mapping 

    def forward(self, sender, frame, datalink_layer):
        print(f"\n[Switch] Frame received from {sender.name} (Port: {sender.name})")

        # 1. ADDRESS LEARNING: Map the sender's MAC to the device object 
        if frame.source_mac not in self.mac_table:
            self.mac_table[frame.source_mac] = sender
            print(f"[Switch] LEARNING: MAC {frame.source_mac} is on port connected to {sender.name}")

        # 2. LOOKUP: Check if the destination MAC is already in our table [cite: 20, 25]
        if frame.dest_mac in self.mac_table:
            dest_device = self.mac_table[frame.dest_mac]
            print(f"[Switch] UNICAST: Found MAC {frame.dest_mac} in table. Forwarding to {dest_device.name}")
            
            # Use the DLL's physical layer to transmit [cite: 7, 10]
            datalink_layer.physical_layer.transmit(self, dest_device, frame)
        
        else:
            # 3. FLOODING: First time seeing this MAC? Send to everyone except sender [cite: 14, 15, 20]
            print(f"[Switch] FLOODING: Unknown destination {frame.dest_mac}. Broadcasting to all ports.")
            for device in self.ports:
                if device != sender:
                    datalink_layer.physical_layer.transmit(self, device, frame)


class Bridge(Device):
    def __init__(self, name):
        super().__init__(name)
        self.mac_table = {}

    def forward(self, sender, frame, datalink_layer):
        print(f"\n[Bridge] Frame received from {sender.name}")

        # Learn MAC
        self.mac_table[frame.source_mac] = sender

        # Forward or filter
        for device in self.ports:
            if device != sender:
                if frame.dest_mac == device.mac_address:
                    print(f"[Bridge] Forwarding to {device.name}")
                    datalink_layer.physical_layer.transmit(sender, device, frame)
                    return

        print("[Bridge] Destination unknown → Flooding")
        for device in self.ports:
            if device != sender:
                datalink_layer.physical_layer.transmit(sender, device, frame)