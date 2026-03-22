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

        self.preamble = "10101011"      # For the Physical Layer teammate

# Create hub and end_device/switch class that inherits from this... for physical/data link layer
class Device:
    def __init__(self, name):
        self.name = name # Readable names like A, B, switch1
        self.mac_address = hex(uuid.getnode()) + name[-1] # Simple unique MAC
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

    def broadcast(self, sender, frame, physical_layer,datalink_layer): # hub broadcast data to all devices
        print(f"\n[Hub] Broadcasting data from {sender.name}...")

        for device in self.ports: # loop for every device which is connected to hub
            if device != sender: # sends data to all except sender
                 datalink_layer.physical_layer.transmit(sender, device, frame) # data transmit through phy layer