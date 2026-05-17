class IPPacket:
    """
    Represents a Layer 3 IPv4 Datagram
    """

    def __init__(self, source_ip, destination_ip, payload,
                 ttl=8, protocol="IPv4"):

        self.source_ip = source_ip
        self.destination_ip = destination_ip
        self.payload = payload
        self.ttl = ttl
        self.protocol = protocol

    def __str__(self):
        return (
            f"[IPPacket] "
            f"{self.source_ip} -> {self.destination_ip} | "
            f"TTL={self.ttl} | "
            f"Protocol={self.protocol} | "
            f"Data={self.payload}"
        )

class NetworkLayer:
    def __init__(self, datalink_layer):
        self.dll = datalink_layer

    def send(self, sender, receiver, message):
        print(f"\n[Network Layer] {sender.name} initiating transmission to {receiver.name}")
        print(f"[Network Layer] Target IP: {receiver.ip_address}")
        
        # ARP logic demonstration (if the device has it)
        if hasattr(sender, 'resolve_arp'):
            mac = sender.resolve_arp(receiver.ip_address)
            if not mac:
                print(f"[Network Layer] ARP Miss. (Simulation continues using DataLink logic)")

        # Pass down to Data Link Layer
        self.dll.send(sender, receiver, message)