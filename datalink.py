from core import Frame, Hub, Switch, Bridge, Router
from network import IPPacket


class DataLinkLayer:

    def __init__(self, physical_layer):

        self.physical_layer = physical_layer

        self.access_protocol = None
        self.flow_control_protocol = None

        self.sent_frames = 0
        self.received_frames = 0

        self.mac_table = {}
        self.transport_layer = None

        # --- RIYANSHI: Add reference to Transport Layer ---
        self.transport_layer = None
    

    # RIYANSHI---
    def set_transport_layer(self, transport_layer):
        self.transport_layer = transport_layer

    # ---------------------------------------------------
    # Protocol Setters
    # ---------------------------------------------------

    def set_access_protocol(self, protocol):

        self.access_protocol = protocol

    def set_flow_control_protocol(self, protocol):

        self.flow_control_protocol = protocol

    # ---------------------------------------------------
    # SEND
    # ---------------------------------------------------

    def send(self, sender, receiver, packet):

        print(f"\n========== DATA LINK LAYER ==========")

        print(f"\n[Data Link Layer] Preparing Frame")

        frames = []

        # -----------------------------------------------
        # SAME SUBNET CHECK
        # -----------------------------------------------

        if sender.ip_address and receiver.ip_address:

            same_subnet = (
                sender.subnet_mask == receiver.subnet_mask and
                sender.ip_address.split('.')[:3] ==
                receiver.ip_address.split('.')[:3]
            )

        else:

            same_subnet = True

        # -----------------------------------------------
        # DEFAULT DESTINATION MAC
        # -----------------------------------------------

        dest_mac = receiver.mac_address

        # -----------------------------------------------
        # ROUTER FORWARDING
        # -----------------------------------------------

        if not same_subnet:

            router = None

            for p in sender.ports:

                if hasattr(p, "routing_table"):

                    router = p
                    break

                elif hasattr(p, "ports"):

                    for sp in p.ports:

                        if hasattr(sp, "routing_table"):

                            router = sp
                            break

                if router:
                    break

            if router:

                print(f"[Network Layer] Remote subnet detected.")
                print(f"[Network Layer] Sending packet to gateway {router.name}")

                for port, iface in router.interfaces.items():

                    if iface["connected"] == sender:

                        dest_mac = iface["mac"]

        # -----------------------------------------------
        # CREATE FRAME
        # -----------------------------------------------

        frame = Frame(
            sender.mac_address,
            dest_mac,
            packet
        )

        frame.is_ack = False

        # Default sequence number
        if not hasattr(frame, "seq_num"):
            frame.seq_num = 0

        self.add_error_detection(frame)

        print(f"\n[Data Link Layer] Frame Created")

        print(f"Source MAC      : {frame.source_mac}")
        print(f"Destination MAC : {frame.dest_mac}")
        print(f"Payload          : {frame.payload}")

        frames.append(frame)

        # -----------------------------------------------
        # FIND CONNECTED DEVICE
        # -----------------------------------------------

        connected_device = next(
            (
                p for p in sender.ports
                if isinstance(p, (Hub, Switch, Bridge, Router))
            ),
            None
        )

        # -----------------------------------------------
        # FLOW CONTROL
        # -----------------------------------------------

        if self.flow_control_protocol and not frame.is_ack:

            target = connected_device if connected_device else receiver

            self.flow_control_protocol.send(
                sender,
                target,
                frames
            )

            self.sent_frames += len(frames)

            return

        # -----------------------------------------------
        # NORMAL TRANSMISSION
        # -----------------------------------------------

        for frame in frames:

            if self.access_protocol and connected_device:

                self.access_protocol.handle_access(
                    sender,
                    connected_device,
                    frame,
                    self.physical_layer
                )

            elif isinstance(connected_device, Switch):

                connected_device.forward(
                    sender,
                    frame,
                    self
                )

            elif isinstance(connected_device, Hub):

                connected_device.broadcast(
                    sender,
                    frame,
                    self
                )

            elif isinstance(connected_device, Router):

                connected_device.forward(
                    sender,
                    frame,
                    self
                )

            else:

                self.physical_layer.transmit(
                    sender,
                    receiver,
                    frame,
                    self
                )

            self.sent_frames += 1

    # ---------------------------------------------------
    # RECEIVE
    # ---------------------------------------------------

    def receive(self, receiver, frame):

        print(f"\n========== DATA LINK LAYER RECEIVE ==========")

        print(f"\n[Data Link Layer] {receiver.name} received a frame.")

        # -----------------------------------------------
        # ERROR CHECKING
        # -----------------------------------------------

        if not frame.is_ack:

            calculated = sum(
                ord(c)
                for c in str(frame.payload)
            ) % 256

            if calculated == frame.error_code:

                print("[Data Link Layer] No error detected.")

            else:

                print("[Data Link Layer] Error detected!")
                print("[Data Link Layer] Frame discarded.")

                return

        # -----------------------------------------------
        # ACK LOGIC
        # -----------------------------------------------

        if not frame.is_ack:

            print(
                f"[Data Link Layer] "
                f"{receiver.name} sending ACK frame "
                f"for Seq {frame.seq_num}"
            )

            self.send_ack(
                receiver,
                frame.source_mac,
                frame.seq_num,
                frame.payload
            )

        else:

            print(
                f"[Data Link Layer] "
                f"ACK {frame.seq_num} received successfully."
            )

        self.received_frames += 1

        # -----------------------------------------------
        # NETWORK LAYER DECAPSULATION
        # -----------------------------------------------

        if isinstance(frame.payload, IPPacket):

            packet = frame.payload

            print("\n========== NETWORK LAYER RECEIVE ==========")

            print(packet)

            # --- MEMBER 3: Trigger Real Transport Engine Flow ---
            # Purane static application layer prints ko hata kar 
            # packet ko direct transport engine ke pass bhejien.
            if self.transport_layer:
                self.transport_layer.receive(packet)
            else:
                # Fallback agar main.py se direct transport link na ho
                segment = packet.payload
                print("\n========== TRANSPORT LAYER RECEIVE ==========")
                print(segment)
                print(f"[Transport Layer] Destination Port: {segment.dest_port}")
                print(f"[Application Layer] Delivered Data: {segment.data}")
                

    # ---------------------------------------------------
    # ERROR DETECTION
    # ---------------------------------------------------

    def add_error_detection(self, frame):

        frame.error_code = sum(
            ord(c)
            for c in str(frame.payload)
        ) % 256

    def check_error(self, frame):

        calculated = sum(
            ord(c)
            for c in str(frame.payload)
        ) % 256

        return calculated == frame.error_code

    # ---------------------------------------------------
    # ACK SENDER
    # ---------------------------------------------------

    def send_ack(
        self,
        sender,
        receiver_mac,
        seq_num,
        original_payload=None
    ):

        print(
            f"\n[Data Link Layer] "
            f"{sender.name} is sending ACK "
            f"for Seq {seq_num}"
        )

        # -----------------------------------------------
        # ACK FRAME CREATION
        # -----------------------------------------------

        if isinstance(original_payload, IPPacket):

            ack_packet = IPPacket(
                source_ip=original_payload.destination_ip,
                destination_ip=original_payload.source_ip,
                payload=f"ACK {seq_num}",
                protocol="ACK"
            )

            ack_frame = Frame(
                sender.mac_address,
                receiver_mac,
                ack_packet
            )

        else:

            ack_frame = Frame(
                sender.mac_address,
                receiver_mac,
                "ACK"
            )

        ack_frame.is_ack = True
        ack_frame.seq_num = seq_num

        # -----------------------------------------------
        # FIND CONNECTED DEVICE
        # -----------------------------------------------

        connected_device = next(
            (
                p for p in sender.ports
                if isinstance(p, (Hub, Switch, Bridge, Router))
            ),
            None
        )

        # -----------------------------------------------
        # SEND ACK
        # -----------------------------------------------

        if isinstance(connected_device, (Switch, Router)):

            connected_device.forward(
                sender,
                ack_frame,
                self
            )

        elif isinstance(connected_device, Hub):

            connected_device.broadcast(
                sender,
                ack_frame,
                self
            )

        else:

            receiver_device = next(
                (
                    p for p in sender.ports
                    if hasattr(p, "mac_address")
                    and p.mac_address == receiver_mac
                ),
                None
            )

            if receiver_device:

                self.physical_layer.transmit(
                    sender,
                    receiver_device,
                    ack_frame,
                    self
                )

            else:

                print(
                    "[Data Link Layer] ERROR: "
                    "Receiver device not found for ACK!"
                )

    # ---------------------------------------------------
    # STATS
    # ---------------------------------------------------

    def stats(self):

        print("\n--- Data Link Layer Stats ---")

        print(f"Frames Sent     : {self.sent_frames}")
        print(f"Frames Received : {self.received_frames}")