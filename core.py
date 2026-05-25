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
        self.ip_address = None  # User assigned (e.g., "192.168.1.10")
        self.subnet_mask = None # To identify network (e.g., "255.255.255.0")
        self.arp_table = {}     # IP to MAC mapping dictionary: {"192.168.1.10": "0x4fbc..."}

    def connect(self, other_device):
        """Creates a physical connection between two devices"""
        if other_device not in self.ports:
            self.ports.append(other_device)
            other_device.ports.append(self)
            print(f"Connected {self.name} <---> {other_device.name}")
     

    # --- To check ARP table  ---
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
        unique_networks = set()

        from network_utils import get_network_address

        for dev in self.all_devices.values():

            if isinstance(dev, Switch):
                # Each switch port is a separate collision domain
                collision_domains += len(dev.ports)

            elif isinstance(dev, Hub):
                # Entire hub forms one collision domain
                collision_domains += 1

            elif isinstance(dev, Router):

                for port, iface in dev.interfaces.items():

                    # Calculate network address of router interface
                    net_addr = get_network_address(
                        iface["ip"],
                        iface["mask"]
                    )

                    # Add network to broadcast domain set
                    unique_networks.add(net_addr)

                    # Check connected device
                    connected_dev = iface.get("connected")

                    # Count collision domain only for directly connected end devices
                    if (
                        connected_dev
                        and not isinstance(connected_dev, (Switch, Hub, Router))
                    ):
                        collision_domains += 1

        # Number of broadcast domains
        broadcast_domains = (
            len(unique_networks)
            if len(unique_networks) > 0
            else 1
        )
                
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
                    datalink_layer.physical_layer.transmit(self,device,frame,datalink_layer)
                    return

        print("[Bridge] Destination unknown → Flooding")
        for device in self.ports:
            if device != sender:
                datalink_layer.physical_layer.transmit(self,device,frame,datalink_layer)

class Router(Device):
    def __init__(self, name):
        super().__init__(name)

        # Format: { port_index: {"ip": ip, "mask": mask, "mac": unique_mac, "connected_device": dev} }
        self.interfaces = {} 
            
        # Static/Dynamic Routing Table (List of tuples/dicts)
        # Format: [(Network, Mask, Output_Port)]
        self.routing_table = [] 

    def configure_interface(self, port_index, ip, mask, connected_device):
        """[Router Configuration] Router ke alag-alag ports par IP aur Subnet mask set karna."""
        import uuid
        if_mac = hex(uuid.uuid4().int)[:12] # unique MAC address for each port
            
        self.interfaces[port_index] = {
            "ip": ip,
            "mask": mask,
            "mac": if_mac,
            "connected": connected_device
        }
        # making physical connections
        self.connect(connected_device)
        print(f"[Router Config] Interface {port_index} on {self.name} configured with IP {ip} ({mask})")

    def forward(self, sender, frame, datalink_layer):
        """
        Core Layer 3 Forwarding Logic
        """
        # Enforce destination MAC check at Layer 2 for the router interfaces and router device MAC
        allowed_macs = [iface["mac"] for iface in self.interfaces.values()]
        allowed_macs.append(self.mac_address)
        allowed_macs.append("ffffffffffff")
        if frame.dest_mac not in allowed_macs:
            print(f"❌ [Router {self.name}] Frame destination MAC {frame.dest_mac} mismatch. Discarding at Layer 2.")
            return

        packet = frame.payload

        if isinstance(packet, str) and packet.startswith("RIP_UPDATE|"):
            if hasattr(self, 'rip_engine'):
                incoming_port = None
                sender_ip = None
                # Find incoming port on self
                for port, iface in self.interfaces.items():
                    if iface["connected"] == sender:
                        incoming_port = port
                        break
                # Find sender's IP on the connecting interface
                if hasattr(sender, 'interfaces'):
                    for sp, s_iface in sender.interfaces.items():
                        if s_iface["connected"] == self:
                            sender_ip = s_iface["ip"]
                            break
                            
                self.rip_engine.process_rip_update(sender_ip, packet, incoming_port)
            return

        if getattr(frame, "is_ack", False) and isinstance(frame.payload, str):
            # Local Layer 2 ACKs are absorbed. Routed Layer 3 ACKs continue.
            return

        print(f"\n[Router {self.name}] Received packet:")
        print(packet)

        # STEP 1: TTL Check
        packet.ttl -= 1

        if packet.ttl <= 0:
            print("[Router] Packet dropped! TTL expired.")
            return

        from network_utils import get_network_address

        for port, iface in self.interfaces.items():

            net_addr = get_network_address(
                packet.destination_ip,
                iface["mask"]
            )

            own_network = get_network_address(
                iface["ip"],
                iface["mask"]
            )

            if net_addr == own_network:

                next_device = iface["connected"]
                target_mac = next_device.mac_address
                
                # Mock ARP for local delivery across a switch
                if hasattr(next_device, "ports"):
                    for p in next_device.ports:
                        if getattr(p, "ip_address", None) == packet.destination_ip:
                            target_mac = p.mac_address
                            break

                new_frame = Frame(
                    iface["mac"],
                    target_mac,
                    packet
                )
                new_frame.is_ack = getattr(frame, "is_ack", False)
                new_frame.seq_num = getattr(frame, "seq_num", None)

                print(f"[Router] Destination is directly connected.")
                print(f"[Router] Sending directly to {next_device.name}")

                datalink_layer.add_error_detection(new_frame) # Recalculate checksum
                datalink_layer.physical_layer.transmit(
                    self,
                    next_device,
                    new_frame,
                    datalink_layer
                )

                return

        print(f"[Router] TTL decremented to {packet.ttl}")

        # STEP 2: Longest Prefix Matching
        best_route = None

        if hasattr(self, 'rip_engine'):
            # Use dynamic routing table
            best_match = self.rip_engine.longest_prefix_match(packet.destination_ip)
            if best_match:
                best_route = (best_match.network, best_match.mask, best_match.interface_port)
        else:
            # Use static routing table
            longest_mask = -1
            from network_utils import get_network_address
            for network, mask, out_port in self.routing_table:
                net_addr = get_network_address(packet.destination_ip, mask)
                if net_addr == network:
                    mask_length = sum(bin(int(x)).count("1") for x in mask.split("."))
                    if mask_length > longest_mask:
                        longest_mask = mask_length
                        best_route = (network, mask, out_port)

        # STEP 3: Route Validation
        if not best_route:
            print("[Router] No route found for destination.")
            return

        network, mask, out_port = best_route

        print(f"[Router] Route matched:")
        print(f"Destination Network: {network}/{mask}")
        print(f"Outgoing Interface: {out_port}")

        # STEP 4: Find Next Device
        next_device = self.interfaces[out_port]["connected"]

        # STEP 5: Create NEW Frame
        new_frame = Frame(
            self.interfaces[out_port]["mac"],
            next_device.mac_address,
            packet
        )
        new_frame.is_ack = getattr(frame, "is_ack", False)
        new_frame.seq_num = getattr(frame, "seq_num", None)

        print(f"[Router] Forwarding packet to {next_device.name}")

        # STEP 6: Send Frame
        datalink_layer.add_error_detection(new_frame) # Recalculate checksum
        datalink_layer.physical_layer.transmit(
            self,
            next_device,
            new_frame,
            datalink_layer
        )          
