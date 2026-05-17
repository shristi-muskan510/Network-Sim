from core import Frame, Hub, Switch, Bridge,Router
from network import IPPacket

class DataLinkLayer:
    def __init__(self, physical_layer):
        self.physical_layer = physical_layer
        self.access_protocol = None
        self.flow_control_protocol = None
        self.sent_frames = 0
        self.received_frames = 0
        self.mac_table = {} 

    def set_access_protocol(self, protocol):
        self.access_protocol = protocol

    def set_flow_control_protocol(self, protocol):
        self.flow_control_protocol = protocol

    def send(self, sender, receiver, message):
        print(f"\n[Data Link Layer] Preparing to send: '{message}'")
        frames = []
        for char in message:
            packet = IPPacket(
                sender.ip_address,
                receiver.ip_address,
                char
            )

            # Same subnet check
            same_subnet = (
                sender.subnet_mask == receiver.subnet_mask and
                sender.ip_address.split('.')[:3] ==
                receiver.ip_address.split('.')[:3]
            )

            # Default destination MAC
            dest_mac = receiver.mac_address

            # If remote subnet, send to router
            if not same_subnet:

                router = next(
                    (
                        p for p in sender.ports
                        if hasattr(p, "routing_table")
                    ),
                    None
                )

                if router:
                    print(f"[Network Layer] Remote subnet detected.")
                    print(f"[Network Layer] Sending packet to gateway {router.name}")

                    # Find router interface connected to sender subnet
                    for port, iface in router.interfaces.items():

                        if iface["connected"] == sender:
                            dest_mac = iface["mac"]


            f = Frame(
                sender.mac_address,
                dest_mac,
                packet
            )
            f.is_ack = False
            # Skipping error_detection for ACKs
            
            self.add_error_detection(f)

            print(f"Frame Payload: {f.payload}")

            frames.append(f)

        connected_device = next((p for p in sender.ports if isinstance(p, (Hub, Switch, Bridge,Router))), None)

        if self.flow_control_protocol and len(frames) > 1 and not frames[0].is_ack:
            target = connected_device if connected_device else receiver
            self.flow_control_protocol.send(sender, target, frames)
            self.sent_frames += len(frames)
            return

        for frame in frames:
            if self.access_protocol and connected_device:
                self.access_protocol.handle_access(sender, connected_device, frame, self.physical_layer)
            elif isinstance(connected_device, Switch):
                connected_device.forward(sender, frame, self)
            elif isinstance(connected_device, Hub):
                connected_device.broadcast(sender, frame, self)
            elif isinstance(connected_device, Router):
                connected_device.forward(sender, frame, self)
            else:
                self.physical_layer.transmit(sender, receiver, frame,self)
            self.sent_frames += 1

    def receive(self, receiver, frame):
        print(f"\n[Data Link Layer] {receiver.name} received a frame.")

        if not frame.is_ack:

            calculated = sum(ord(c) for c in str(frame.payload)) % 256

            if calculated == frame.error_code:
                print("[Data Link Layer] No error detected.")
            else:
                print("[Data Link Layer] Error detected! Frame discarded.")
                return

        # ADDRESS LEARNING TRIGGER
        if not frame.is_ack:
            print(f"[Data Link Layer] {receiver.name} sending actual ACK frame for Seq {frame.seq_num}")
            # Sending back ACK frames for Switch to learn MAC address of receiver.
            self.send_ack(receiver, frame.source_mac, frame.seq_num)
        else:
            print(f"[Data Link Layer] ACK {frame.seq_num} received successfully.")

        self.received_frames += 1

    def add_error_detection(self, frame):
        frame.error_code = sum(ord(c) for c in str(frame.payload)) % 256

    def check_error(self, frame):
        calculated = sum(ord(c) for c in str(frame.payload)) % 256
        return calculated == frame.error_code

    def send_ack(self, sender, receiver_mac, seq_num):
    # sender: Device sending ACK
    # receiver_mac: Device who should recevive ACK (Original Sender)
        print(f"\n[Data Link Layer] {sender.name} is sending ACK for Seq {seq_num}")
    
    # 1. Make ACK frames(Source = sender, Dest = original sender's MAC)
        ack_frame = Frame(sender.mac_address, receiver_mac, "ACK")
        ack_frame.is_ack = True
        ack_frame.seq_num = seq_num

    # 2. Intermediate device (Switch/Hub) connected to sender
        connected_device = next((p for p in sender.ports if isinstance(p, (Hub, Switch, Bridge,Router))), None)

    # 3. Sending ACK through switch for learning address
        if isinstance(connected_device, (Switch,Router)):
        # Switch will learn 'sender' address and forward the ACK
            connected_device.forward(sender, ack_frame, self)
        elif isinstance(connected_device, Hub):
            connected_device.broadcast(sender, ack_frame, self)
        else:
        # If no intermidiate device, send directly
            receiver_device = self.mac_table.get(receiver_mac)
            if receiver_device:
                self.physical_layer.transmit(sender, receiver_device, ack_frame, self)
            else:
                print("[Data Link Layer] ERROR: Receiver device not found for ACK!")

    def stats(self):
        print("\n--- Data Link Layer Stats ---")
        print(f"Frames Sent: {self.sent_frames}")
        print(f"Frames Received: {self.received_frames}")