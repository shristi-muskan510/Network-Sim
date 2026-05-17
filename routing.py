import sys

class RIPEntry:
    """Represents a single row in the RIP Routing Table."""
    def __init__(self, network, mask, next_hop, metric, interface_port):
        self.network = network          # e.g., "192.168.1.0"
        self.mask = mask                # e.g., "255.255.255.0"
        self.next_hop = next_hop        # IP of the adjacent router interface, or "Direct"
        self.metric = metric            # Hop count (1 to 15, 16 = Infinity)
        self.interface_port = interface_port  # Local router interface index (0, 1, etc.)

    def __repr__(self):
        return f"Network: {self.network}/{self.mask} | Next Hop: {self.next_hop} | Metric: {self.metric} | Port: {self.interface_port}"


class RIPRoutingEngine:
    def __init__(self, router):
        self.router = router  # Reference to the parent Router object
        self.router.rip_engine = self
        self.routing_table = {}  # Key: Network string, Value: RIPEntry object
        self.MAX_HOPS = 16  # 16 means infinity / network unreachable

    def initialize_local_routes(self):
        """
        Reads the router's directly connected interfaces and populates 
        the initial routing table with a metric of 1.
        """
        from network_utils import get_network_address
        
        for port, iface in self.router.interfaces.items():
            ip = iface["ip"]
            mask = iface["mask"]
            net_addr = get_network_address(ip, mask)
            
            if net_addr:
                # Directly connected networks have a hop count metric of 1
                self.routing_table[net_addr] = RIPEntry(
                    network=net_addr,
                    mask=mask,
                    next_hop="Direct",
                    metric=1,
                    interface_port=port
                )
        print(f"[{self.router.name} RIP] Initialized directly connected subnets.")

    def ip_to_bin(self, ip_str):
        """Helper to convert an IP address string to a 32-bit binary string."""
        return "".join(format(int(x), '08b') for x in ip_str.split('.'))

    def longest_prefix_match(self, dest_ip):
        """
        Executes the Longest Mask Matching algorithm for packet forwarding.
        Returns the best matching RIPEntry or None.
        """
        dest_bin = self.ip_to_bin(dest_ip)
        best_match = None
        longest_mask_length = -1

        for net_addr, entry in self.routing_table.items():
            if entry.metric >= self.MAX_HOPS:
                continue # Ignore unreachable networks
            
            mask_bin = self.ip_to_bin(entry.mask)
            net_bin = self.ip_to_bin(entry.network)
            
            # Count mask length (number of 1s)
            mask_len = mask_bin.count('1')
            
            # Bitwise AND simulation
            matches = True
            for i in range(32):
                if mask_bin[i] == '1':
                    if dest_bin[i] != net_bin[i]:
                        matches = False
                        break
            
            if matches:
                # If it's a valid match and has a more specific subnet mask, choose it
                if mask_len > longest_mask_length:
                    longest_mask_length = mask_len
                    best_match = entry

        return best_match

    def generate_update_payload(self):
        """
        Serializes the routing table data into a payload format 
        that can be embedded inside a standard Frame object.
        """
        # Format: NETWORK,MASK,METRIC
        entries = []
        for net, entry in self.routing_table.items():
            entries.append(f"{entry.network}:{entry.mask}:{entry.metric}")
        return "RIP_UPDATE|" + ";".join(entries)

    def send_rip_updates(self, datalink_layer):
        """
        Simulates Distance-Vector broadcasting. Sends the routing table 
        to all adjacent devices connected to the router's ports.
        """
        payload = self.generate_update_payload()
        print(f"\n[{self.router.name} RIP] Broadcasting routing table updates to neighbors...")
        
        for port, iface in self.router.interfaces.items():
            connected_dev = iface.get("connected")
            if connected_dev:
                # Create a specific routing protocol Frame
                # Using dummy broadcast MAC target since it's an interior network advertisement
                from core import Frame
                rip_frame = Frame(
                    source_mac=iface["mac"], 
                    dest_mac="ffffffffffff", 
                    data=payload
                )
                rip_frame.is_ack = True # Bypass ACK response triggers in DLL
                
                print(f" -> Sending update via interface {port} to {connected_dev.name}")
                datalink_layer.physical_layer.transmit(self.router, connected_dev, rip_frame, datalink_layer)

    def process_rip_update(self, sender_ip, payload, incoming_port):
        """
        Bellman-Ford Algorithm Implementation. Updates the local routing table 
        if a shorter path to a distant network is advertised by a neighbor.
        """
        raw_data = payload.split("|")[1]
        if not raw_data:
            return
            
        advertised_entries = raw_data.split(";")
        table_changed = False

        for adv in advertised_entries:
            if not adv:
                continue
            net, mask, metric_str = adv.split(":")
            advertised_metric = int(metric_str)
            
            # Bellman-Ford increments hop count by 1 for the transit link
            new_metric = advertised_metric + 1
            if new_metric > self.MAX_HOPS:
                new_metric = self.MAX_HOPS

            # Checking if network already exists in local table
            if net in self.routing_table:
                existing_entry = self.routing_table[net]
                
                # Rule 1: Update if the new path offers a lower hop count cost
                # Rule 2: If the update comes from the SAME next-hop router, update even if cost is worse (topology shift)
                if new_metric < existing_entry.metric or existing_entry.next_hop == sender_ip:
                    if existing_entry.metric != new_metric or existing_entry.next_hop != sender_ip:
                        existing_entry.metric = new_metric
                        existing_entry.next_hop = sender_ip
                        existing_entry.interface_port = incoming_port
                        table_changed = True
            else:
                # New undiscovered network found! Add to table.
                if new_metric < self.MAX_HOPS:
                    self.routing_table[net] = RIPEntry(
                        network=net,
                        mask=mask,
                        next_hop=sender_ip,
                        metric=new_metric,
                        interface_port=incoming_port
                    )
                    table_changed = True

        if table_changed:
            print(f"✅ [{self.router.name} RIP] Routing Table UPDATED via advertisement from {sender_ip}!")
            self.display_table()

    def display_table(self):
        """Utility to pretty-print the dynamic routing states."""
        print(f"\n=== RIP ROUTING TABLE FOR {self.router.name} ===")
        print(f"{'Destination Net':<16} {'Subnet Mask':<16} {'Next Hop':<15} {'Metric':<6} {'Port':<4}")
        print("-" * 62)
        for net, entry in self.routing_table.items():
            print(f"{entry.network:<16} {entry.mask:<16} {entry.next_hop:<15} {entry.metric:<6} {entry.interface_port:<4}")
        print("=" * 62)