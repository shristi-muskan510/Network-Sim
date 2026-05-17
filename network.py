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