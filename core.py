import uuid

class Frame:
    """The universal data object shared by all layers."""
    def __init__(self, source_mac, dest_mac, data, error_bit=0):
        self.source_mac = source_mac
        self.dest_mac = dest_mac
        self.payload = data

        self.error_code = None
        self.seq_num = 0
        self.is_ack = False

        self.preamble = "10101010" 
class Device:
    def __init__(self, name):
        self.name = name # Readable names like A, B, switch1
        self.mac_address = hex(uuid.uuid4().int)[:12] # Simple unique MAC
        self.ports = [] # Connections to other devices

        # --- RIYANSHI: Network Layer Additions ---
        self.ip_address = None     # User assign karega (e.g., "192.168.1.10")
        self.subnet_mask = None    # Network pehchane ke liye (e.g., "255.255.255.0")
        self.arp_table = {}        # IP to MAC mapping dictionary: {"192.168.1.10": "0x4fbc..."}

    def connect(self, other_device):
        """Creates a physical connection between two devices"""
        if other_device not in self.ports:
            self.ports.append(other_device)
            other_device.ports.append(self)
            print(f"Connected {self.name} <---> {other_device.name}")
     

    # --- RIYANSHI: fun to check ARP table  ---
    def resolve_arp(self, target_ip):
        """
        [ARP Logic] IP address ke badle MAC address dhoodhta hai.
        """
        print(f"\n[ARP] {self.name} checking local ARP cache for IP: {target_ip}")
        if target_ip in self.arp_table:
            print(f"[ARP] Cache HIT! Found: {target_ip} -> {self.arp_table[target_ip]}")
            return self.arp_table[target_ip]
        
        print(f"[ARP] Cache MISS for {target_ip}! Needs to broadcast ARP Request.")
        return None


class SimulatorCore:
    def __init__(self):
        self.all_devices = {}

    def add_device(self, device_obj):
        self.all_devices[device_obj.name] = device_obj


    def get_stats(self):
        collision_domains = 0
        broadcast_domains = 1
        
        for dev in self.all_devices.values():
            if isinstance(dev, Switch):
                # Each connected device on a switch is its own collision domain 
                collision_domains += len(dev.ports)
            elif isinstance(dev, Hub):
                # A hub is one single collision domain 
                collision_domains += 1
                
        print(f"\n--- Network Report ---")
        print(f"Collision Domains: {collision_domains}")
        print(f"Broadcast Domains: {broadcast_domains}")


class Hub(Device): # hub is a netowrking device which inherits from Device 
    def __init__(self, name):
        super().__init__(name)

    def broadcast(self, sender, frame, datalink_layer): # broadcasting data to all devices
        print(f"\n[Hub] Broadcasting data from {sender.name}...")

        for device in self.ports: # loop for every device which is connected to hub
            if device != sender: # sends data to all except sender
                datalink_layer.physical_layer.transmit(self, device, frame, datalink_layer)


class Switch(Device):
    def __init__(self, name):
        super().__init__(name)
        self.mac_table = {}

    def forward(self, sender, frame, datalink_layer):
        print(f"\n[Switch] Frame received from {sender.name} (Port: {sender.name})")

        # 1. ADDRESS LEARNING: Map the sender's MAC to the device object 
        if frame.source_mac not in self.mac_table:
            self.mac_table[frame.source_mac] = sender
            print(f"[Switch] LEARNING: MAC {frame.source_mac} is on port connected to {sender.name}")

        # 2. LOOKUP: Check if the destination MAC is already in our table 
        if frame.dest_mac in self.mac_table:
            dest_device = self.mac_table[frame.dest_mac]
            print(f"[Switch] UNICAST: Found MAC {frame.dest_mac} in table. Forwarding to {dest_device.name}")
            datalink_layer.physical_layer.transmit(self, dest_device, frame,datalink_layer)
        
        # 3. FLOODING: First time seeing this MAC? Send to everyone except sender
        else:
            print(f"[Switch] FLOODING: Unknown destination {frame.dest_mac}. Broadcasting to all ports.")
            for device in self.ports:
                if device != sender:
                    datalink_layer.physical_layer.transmit(self, device, frame,datalink_layer)


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



    # --- RIYANSHI: inherited by Device (multiple interfaces of router and routing table)  ---
    class Router(Device):
        def __init__(self, name):
            super().__init__(name)
            # Dictionary jo interfaces store karegi
            # Format: { port_index: {"ip": ip, "mask": mask, "mac": unique_mac, "connected_device": dev} }
            self.interfaces = {} 
            
            # Static/Dynamic Routing Table (List of tuples/dicts)
            # Format: [(Network, Mask, Output_Port)] -> Shared with Person 3
            self.routing_table = [] 

        def configure_interface(self, port_index, ip, mask, connected_device):
            """[Router Configuration] Router ke alag-alag ports par IP aur Subnet mask set karna."""
            import uuid
            if_mac = hex(uuid.uuid4().int)[:12] # Har port ka apna unique MAC address
            
            self.interfaces[port_index] = {
                "ip": ip,
                "mask": mask,
                "mac": if_mac,
                "connected": connected_device
            }
            # Purane physical connection logic se connect karo
            self.connect(connected_device)
            print(f"[Router Config] Interface {port_index} on {self.name} configured with IP {ip} ({mask})")          