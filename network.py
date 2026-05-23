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

            mac = sender.resolve_arp(receiver.ip_address)

            if not mac:

                print(
                    "[Network Layer] "
                    "ARP Resolution Failed"
                )

        print(
            "[Network Layer] "
            "Passing packet to Data Link Layer"
        )

        self.dll.send(
            sender,
            receiver,
            ip_packet
        )