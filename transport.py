# riyanshi
from apps import FTPServer, TelnetServer 


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
        ack_num=0,
        is_ack=False,
        is_last=False
    ):

        self.src_port = src_port
        self.dest_port = dest_port
        self.seq_num = seq_num
        self.ack_num = ack_num
        self.data = data
        self.is_ack = is_ack
        self.is_last = is_last

    def __str__(self):
        ack_str = " (ACK)" if self.is_ack else ""
        last_str = " (LAST)" if self.is_last else ""
        return (
            f"\n[TCP Segment{ack_str}{last_str}]\n"
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

        # --- RIYANSHI: Instantiate Application Engines ---
        self.ftp_server = FTPServer()
        self.telnet_server = TelnetServer()

        self.simulator = None

        # Request GBN States
        self.sender_device = None
        self.receiver_device = None
        self.window_size = 3
        self.base = 0
        self.next_seq = 0
        self.segments_to_send = []
        self.received_chunks = {}
        self.expected_seq_num = 0
        self.transmission_complete = False

        # Response GBN States
        self.resp_base = 0
        self.resp_next_seq = 0
        self.resp_segments = []
        self.resp_expected_seq_num = 0
        self.resp_received_chunks = {}

    def set_simulator(self, simulator):
        self.simulator = simulator

    def find_device_by_ip(self, ip):
        if not self.simulator:
            return None
        for dev in self.simulator.all_devices.values():
            if getattr(dev, 'ip_address', None) == ip:
                return dev
            if hasattr(dev, 'interfaces'):
                for iface in dev.interfaces.values():
                    if iface.get("ip") == ip:
                        return dev
        return None

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

        # Segment the data payload into chunks of 4 characters
        chunk_size = 4
        chunks = [data[i:i+chunk_size] for i in range(0, len(data), chunk_size)]
        num_chunks = len(chunks)

        print(f"[Transport GBN] Sender: Original message '{data}' split into {num_chunks} chunks.")

        # Create TCP Segments
        self.segments_to_send = []
        for i, chunk in enumerate(chunks):
            segment = TCPSegment(
                src_port=src_port,
                dest_port=dest_port,
                data=chunk,
                seq_num=i,
                ack_num=0,
                is_ack=False,
                is_last=(i == num_chunks - 1)
            )
            self.segments_to_send.append(segment)

        # Initialize GBN States
        self.sender_device = sender
        self.receiver_device = receiver
        self.base = 0
        self.next_seq = 0
        self.expected_seq_num = 0
        self.received_chunks = {}
        self.transmission_complete = False

        # Go-Back-N sliding window transmission loop
        while self.base < num_chunks:
            while self.next_seq < self.base + self.window_size and self.next_seq < num_chunks:
                seg = self.segments_to_send[self.next_seq]
                print(f"\n[Transport GBN] Sender: Sending Segment {seg.seq_num} / {num_chunks-1}")
                print(seg)

                # Encapsulation into IP Packet
                ip_packet = IPPacket(
                    source_ip=sender.ip_address,
                    destination_ip=receiver.ip_address,
                    payload=seg,
                    ttl=8,
                    protocol=protocol
                )

                print(f"[Transport Layer] Encapsulating segment {seg.seq_num} into IP Packet")

                # Pass to Network Layer
                self.network_layer.send_packet(
                    sender,
                    receiver,
                    ip_packet
                )
                self.next_seq += 1

    def send_app_response(
        self,
        sender,
        receiver,
        response_data,
        dest_port,
        protocol="TCP"
    ):
        print("\n========== TRANSPORT LAYER (SEND RESPONSE) ==========")

        # Well-known server port as source port
        src_port = 21 if "FTP" in response_data else 23

        chunk_size = 4
        chunks = [response_data[i:i+chunk_size] for i in range(0, len(response_data), chunk_size)]
        num_chunks = len(chunks)

        print(f"[Transport GBN] Server: Sending response '{response_data}' split into {num_chunks} chunks.")

        self.resp_segments = []
        for i, chunk in enumerate(chunks):
            seg = TCPSegment(
                src_port=src_port,
                dest_port=dest_port,
                data=chunk,
                seq_num=i,
                ack_num=0,
                is_ack=False,
                is_last=(i == num_chunks - 1)
            )
            self.resp_segments.append(seg)

        self.resp_base = 0
        self.resp_next_seq = 0
        self.resp_expected_seq_num = 0
        self.resp_received_chunks = {}

        while self.resp_base < num_chunks:
            while self.resp_next_seq < self.resp_base + self.window_size and self.resp_next_seq < num_chunks:
                seg = self.resp_segments[self.resp_next_seq]
                print(f"\n[Transport GBN] Server: Sending Response Segment {seg.seq_num} / {num_chunks-1}")
                print(seg)

                ip_packet = IPPacket(
                    source_ip=sender.ip_address,
                    destination_ip=receiver.ip_address,
                    payload=seg,
                    ttl=8,
                    protocol=protocol
                )

                self.network_layer.send_packet(
                    sender,
                    receiver,
                    ip_packet
                )
                self.resp_next_seq += 1

    def receive(self, ip_packet):

        print("\n========== TRANSPORT LAYER RECEIVE ==========")

        segment = ip_packet.payload

        print("[Transport Layer] Segment Received:")
        print(segment)

        # Classification based on direction (Server source vs destination)
        is_from_server = segment.src_port in [21, 23]

        if is_from_server:
            if segment.is_ack:
                # 1. Request ACK Segment (Server -> Client)
                print(f"[Transport GBN] Sender: Received ACK for Request Segment {segment.ack_num}")
                if segment.ack_num >= self.base:
                    self.base = segment.ack_num + 1
                    print(f"[Transport GBN] Sender: Sliding window base to {self.base}")
            else:
                # 2. Response Data Segment (Server -> Client)
                if segment.seq_num == self.resp_expected_seq_num:
                    print(f"[Transport GBN] Client: Response Segment {segment.seq_num} in-order. Buffering.")
                    self.resp_received_chunks[segment.seq_num] = segment.data

                    # Send Transport ACK for response
                    ack_seg = TCPSegment(
                        src_port=segment.dest_port,
                        dest_port=segment.src_port,
                        data="ACK",
                        seq_num=0,
                        ack_num=segment.seq_num,
                        is_ack=True,
                        is_last=False
                    )

                    sender_dev = self.find_device_by_ip(ip_packet.destination_ip)
                    receiver_dev = self.find_device_by_ip(ip_packet.source_ip)

                    print(f"[Transport GBN] Client: Sending ACK for Response Segment {segment.seq_num}")
                    print(ack_seg)

                    ack_packet = IPPacket(
                        source_ip=ip_packet.destination_ip,
                        destination_ip=ip_packet.source_ip,
                        payload=ack_seg,
                        ttl=8,
                        protocol="TCP"
                    )

                    self.network_layer.send_packet(sender_dev, receiver_dev, ack_packet)
                    self.resp_expected_seq_num += 1

                    if segment.is_last:
                        print(f"\n[Transport GBN] Client: All response segments received! Reassembling...")
                        full_response = "".join(self.resp_received_chunks[i] for i in sorted(self.resp_received_chunks.keys()))
                        print(f"\n========== CLIENT APPLICATION LAYER ==========")
                        print(f"[Client Application Output] Response from Server port {segment.src_port}:")
                        print(f"-> {full_response}\n")
                else:
                    print(f"[Transport GBN] Client: Out-of-order response segment {segment.seq_num} (expected {self.resp_expected_seq_num}). Discarding.")
                    if self.resp_expected_seq_num > 0:
                        ack_seg = TCPSegment(
                            src_port=segment.dest_port,
                            dest_port=segment.src_port,
                            data="ACK",
                            seq_num=0,
                            ack_num=self.resp_expected_seq_num - 1,
                            is_ack=True,
                            is_last=False
                        )
                        sender_dev = self.find_device_by_ip(ip_packet.destination_ip)
                        receiver_dev = self.find_device_by_ip(ip_packet.source_ip)
                        ack_packet = IPPacket(
                            source_ip=ip_packet.destination_ip,
                            destination_ip=ip_packet.source_ip,
                            payload=ack_seg,
                            ttl=8,
                            protocol="TCP"
                        )
                        self.network_layer.send_packet(sender_dev, receiver_dev, ack_packet)

        else:
            # Sent to Server (Client -> Server)
            if segment.is_ack:
                # 3. Response ACK Segment (Client -> Server)
                print(f"[Transport GBN] Server: Received ACK for Response Segment {segment.ack_num}")
                if segment.ack_num >= self.resp_base:
                    self.resp_base = segment.ack_num + 1
                    print(f"[Transport GBN] Server: Sliding response window base to {self.resp_base}")
            else:
                # 4. Request Data Segment (Client -> Server)
                if segment.seq_num == self.expected_seq_num:
                    print(f"[Transport GBN] Receiver: Request Segment {segment.seq_num} in-order. Buffering.")
                    self.received_chunks[segment.seq_num] = segment.data

                    # Send Transport ACK for request
                    ack_seg = TCPSegment(
                        src_port=segment.dest_port,
                        dest_port=segment.src_port,
                        data="ACK",
                        seq_num=0,
                        ack_num=segment.seq_num,
                        is_ack=True,
                        is_last=False
                    )

                    sender_dev = self.find_device_by_ip(ip_packet.destination_ip)
                    receiver_dev = self.find_device_by_ip(ip_packet.source_ip)

                    print(f"[Transport GBN] Receiver: Sending ACK for Request Segment {segment.seq_num}")
                    print(ack_seg)

                    ack_packet = IPPacket(
                        source_ip=ip_packet.destination_ip,
                        destination_ip=ip_packet.source_ip,
                        payload=ack_seg,
                        ttl=8,
                        protocol="TCP"
                    )

                    self.network_layer.send_packet(sender_dev, receiver_dev, ack_packet)
                    self.expected_seq_num += 1

                    if segment.is_last:
                        print(f"\n[Transport GBN] Receiver: All request segments received! Reassembling...")
                        full_message = "".join(self.received_chunks[i] for i in sorted(self.received_chunks.keys()))
                        print(f"[Transport GBN] Reassembled Request: '{full_message}'")

                        destination_process = self.process_table.get_process(segment.dest_port)
                        if destination_process:
                            if destination_process == "FTP":
                                print(f"\n========== APPLICATION LAYER (FTP) ==========")
                                app_response = self.ftp_server.handle_request(full_message)
                                print(f"[Application Layer Output] {app_response}")

                            elif destination_process == "TELNET":
                                print(f"\n========== APPLICATION LAYER (TELNET) ==========")
                                app_response = self.telnet_server.handle_request(full_message)
                                print(f"[Application Layer Output] {app_response}")

                            # Send the application response back to the client!
                            self.send_app_response(sender_dev, receiver_dev, app_response, segment.src_port)
                        else:
                            print(f"[Transport Layer] ERROR: No process listening on port {segment.dest_port}")
                else:
                    print(f"[Transport GBN] Receiver: Out-of-order request segment {segment.seq_num} (expected {self.expected_seq_num}). Discarding.")
                    if self.expected_seq_num > 0:
                        ack_seg = TCPSegment(
                            src_port=segment.dest_port,
                            dest_port=segment.src_port,
                            data="ACK",
                            seq_num=0,
                            ack_num=self.expected_seq_num - 1,
                            is_ack=True,
                            is_last=False
                        )
                        sender_dev = self.find_device_by_ip(ip_packet.destination_ip)
                        receiver_dev = self.find_device_by_ip(ip_packet.source_ip)
                        ack_packet = IPPacket(
                            source_ip=ip_packet.destination_ip,
                            destination_ip=ip_packet.source_ip,
                            payload=ack_seg,
                            ttl=8,
                            protocol="TCP"
                        )
                        self.network_layer.send_packet(sender_dev, receiver_dev, ack_packet)

    def show_process_table(self):

        self.process_table.display()