class IPPacket:
    """
    Represents a Layer 3 IPv4 Datagram
    """

    def __init__(
        self,
        source_ip,
        destination_ip,
        payload,
        ttl=8,
        protocol="IPv4"
    ):

        self.source_ip = source_ip
        self.destination_ip = destination_ip
        self.payload = payload
        self.ttl = ttl
        self.protocol = protocol

    def __str__(self):

        return (
            f"\n[IP Packet]\n"
            f"Source IP      : {self.source_ip}\n"
            f"Destination IP : {self.destination_ip}\n"
            f"TTL            : {self.ttl}\n"
            f"Protocol       : {self.protocol}\n"
            f"Payload        : {self.payload}\n"
        )


class NetworkLayer:

    def __init__(self, datalink_layer):

        self.dll = datalink_layer

    def send_packet(
        self,
        sender,
        receiver,
        ip_packet
    ):

        print("\n========== NETWORK LAYER ==========")

        print(ip_packet)

        # Optional ARP simulation
        if hasattr(sender, 'resolve_arp'):
            from network_utils import get_network_address
            
            # Same subnet check
            same_subnet = True
            if sender.ip_address and receiver.ip_address and sender.subnet_mask:
                same_subnet = (
                    sender.subnet_mask == receiver.subnet_mask and
                    sender.ip_address.split('.')[:3] == receiver.ip_address.split('.')[:3]
                )
            
            if same_subnet:
                # Same subnet: Resolve destination directly
                mac = sender.resolve_arp(receiver.ip_address)
                if not mac:
                    print("[Network Layer] Simulating ARP Broadcast Request/Reply...")
                    if hasattr(receiver, 'mac_address') and hasattr(receiver, 'ip_address'):
                        sender.arp_table[receiver.ip_address] = receiver.mac_address
                        print(f"[ARP] {sender.name} learned MAC of {receiver.ip_address} -> {receiver.mac_address}")
                    if hasattr(sender, 'mac_address') and hasattr(sender, 'ip_address'):
                        receiver.arp_table[sender.ip_address] = sender.mac_address
                        print(f"[ARP] {receiver.name} learned MAC of {sender.ip_address} -> {sender.mac_address}")
                    
                    # Resolve again after cache population
                    mac = sender.resolve_arp(receiver.ip_address)
            else:
                # Remote subnet: Resolve default gateway's MAC address instead
                router = None
                gateway_ip = None
                gateway_mac = None
                
                # BFS to find the gateway router connected to our local subnet
                sender_net = get_network_address(sender.ip_address, sender.subnet_mask)
                visited = {sender}
                queue = [sender]
                while queue:
                    curr = queue.pop(0)
                    if hasattr(curr, "interfaces"):  # Router
                        for port, iface in curr.interfaces.items():
                            iface_net = get_network_address(iface["ip"], iface["mask"])
                            if iface_net == sender_net:
                                router = curr
                                gateway_ip = iface["ip"]
                                gateway_mac = iface["mac"]
                                break
                        if router:
                            break
                    
                    if hasattr(curr, "ports"):
                        for neighbor in curr.ports:
                            if neighbor not in visited:
                                # Traverse switches, hubs, bridges, and routers
                                if hasattr(neighbor, "routing_table") or not getattr(neighbor, "ip_address", None):
                                    visited.add(neighbor)
                                    queue.append(neighbor)
                
                if router and gateway_ip:
                    print(f"[Network Layer] Remote subnet detected. Resolving gateway {router.name} ({gateway_ip})...")
                    mac = sender.resolve_arp(gateway_ip)
                    if not mac:
                        print(f"[Network Layer] Simulating ARP Broadcast Request/Reply for Gateway {gateway_ip}...")
                        sender.arp_table[gateway_ip] = gateway_mac
                        print(f"[ARP] {sender.name} learned MAC of Gateway {gateway_ip} -> {gateway_mac}")
                        router.arp_table[sender.ip_address] = sender.mac_address
                        print(f"[ARP] Router {router.name} learned MAC of {sender.ip_address} -> {sender.mac_address}")
                        
                        # Resolve again after cache population
                        mac = sender.resolve_arp(gateway_ip)
                else:
                    # Fallback to direct receiver resolution if no gateway is found
                    mac = sender.resolve_arp(receiver.ip_address)
                    if not mac:
                        print("[Network Layer] Simulating ARP Broadcast Request/Reply...")
                        if hasattr(receiver, 'mac_address') and hasattr(receiver, 'ip_address'):
                            sender.arp_table[receiver.ip_address] = receiver.mac_address
                            print(f"[ARP] {sender.name} learned MAC of {receiver.ip_address} -> {receiver.mac_address}")
                        if hasattr(sender, 'mac_address') and hasattr(sender, 'ip_address'):
                            receiver.arp_table[sender.ip_address] = sender.mac_address
                            print(f"[ARP] {receiver.name} learned MAC of {sender.ip_address} -> {sender.mac_address}")
                        mac = sender.resolve_arp(receiver.ip_address)

        print(
            "[Network Layer] "
            "Passing packet to Data Link Layer"
        )

        self.dll.send(
            sender,
            receiver,
            ip_packet
        )