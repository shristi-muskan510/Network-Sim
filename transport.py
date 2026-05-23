# transport.py

from network import IPPacket


class TCPSegment:
    """
    Simulates a TCP Transport Layer Segment
    """

    def __init__(
        self,
        src_port,
        dest_port,
        data,
        seq_num=0,
        ack_num=0
    ):

        self.src_port = src_port
        self.dest_port = dest_port
        self.seq_num = seq_num
        self.ack_num = ack_num
        self.data = data

    def __str__(self):

        return (
            f"\n[TCP Segment]\n"
            f"Source Port      : {self.src_port}\n"
            f"Destination Port : {self.dest_port}\n"
            f"Sequence Number  : {self.seq_num}\n"
            f"ACK Number       : {self.ack_num}\n"
            f"Payload          : {self.data}\n"
        )


class PortManager:
    """
    Handles:
    - Well-known ports
    - Ephemeral ports
    - Port allocation/release
    """

    WELL_KNOWN_PORTS = {
        "FTP": 21,
        "TELNET": 23
    }

    def __init__(self):

        self.used_ports = set()

        # Reserve well-known ports
        for port in self.WELL_KNOWN_PORTS.values():
            self.used_ports.add(port)

    def allocate_ephemeral_port(self):

        for port in range(49152, 65535):

            if port not in self.used_ports:

                self.used_ports.add(port)

                return port

        raise Exception("No free ephemeral ports available")

    def reserve_port(self, port):

        self.used_ports.add(port)

    def release_port(self, port):

        if port in self.used_ports:
            self.used_ports.remove(port)


class ProcessTable:
    """
    Maps:
    Port Number -> Application/Process Name
    """

    def __init__(self):

        self.processes = {}

    def register_process(self, port, process_name):

        self.processes[port] = process_name

    def get_process(self, port):

        return self.processes.get(port)

    def display(self):

        print("\n[Process Table]")

        for port, process in self.processes.items():

            print(f"Port {port} --> {process}")


class TransportLayer:
    """
    Simulates the Transport Layer
    """

    def __init__(self, network_layer):

        self.network_layer = network_layer

        self.port_manager = PortManager()

        self.process_table = ProcessTable()

        # Register Well-Known Services
        self.process_table.register_process(21, "FTP")
        self.process_table.register_process(23, "TELNET")

    def send(
        self,
        sender,
        receiver,
        data,
        dest_port,
        protocol="TCP"
    ):

        print("\n========== TRANSPORT LAYER ==========")

        # Allocate ephemeral source port
        src_port = self.port_manager.allocate_ephemeral_port()

        print(f"[Transport Layer] Source Port Assigned : {src_port}")
        print(f"[Transport Layer] Destination Port     : {dest_port}")

        # Check destination process
        process = self.process_table.get_process(dest_port)

        if process:

            print(f"[Transport Layer] Destination Service : {process}")

        else:

            print("[Transport Layer] WARNING: No process registered on destination port")

        # Create TCP Segment
        segment = TCPSegment(
            src_port=src_port,
            dest_port=dest_port,
            data=data,
            seq_num=1,
            ack_num=0
        )

        print("\n[Transport Layer] Segment Created:")
        print(segment)

        # Encapsulation into IP Packet
        ip_packet = IPPacket(
            source_ip=sender.ip_address,
            destination_ip=receiver.ip_address,
            payload=segment,
            ttl=8,
            protocol=protocol
        )

        print("[Transport Layer] Encapsulating segment into IP Packet")

        # Pass to Network Layer
        self.network_layer.send_packet(
            sender,
            receiver,
            ip_packet
        )

    def receive(self, ip_packet):

        print("\n========== TRANSPORT LAYER RECEIVE ==========")

        segment = ip_packet.payload

        print("[Transport Layer] Segment Received:")
        print(segment)

        destination_process = self.process_table.get_process(
            segment.dest_port
        )

        if destination_process:

            print(
                f"[Transport Layer] Delivering data to process: "
                f"{destination_process}"
            )

            print(
                f"[Application Layer] Data Received: "
                f"{segment.data}"
            )

        else:

            print(
                f"[Transport Layer] ERROR: "
                f"No process listening on port {segment.dest_port}"
            )

    def show_process_table(self):

        self.process_table.display()