from core import Frame, Hub, Switch, Bridge

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
            f = Frame(sender.mac_address, receiver.mac_address, char)
            f.is_ack = False
            # ACK frames ke liye error detection skip kar sakte hain ya simple rakh sakte hain
            
            self.add_error_detection(f)
            print(f"Frame Payload: {f.payload}, Checksum: {f.error_code}")

            frames.append(f)

        connected_device = next((p for p in sender.ports if isinstance(p, (Hub, Switch, Bridge))), None)

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
            else:
                self.physical_layer.transmit(sender, receiver, frame,self)
            self.sent_frames += 1

    def receive(self, receiver, frame):
        print(f"\n[Data Link Layer] {receiver.name} received a frame.")

        self.mac_table[frame.source_mac] = receiver

        if not frame.is_ack and not self.check_error(frame):
            print("[Data Link Layer] Error detected! Frame discarded.")
            return

        # YAHI HAI ADDRESS LEARNING KA TRIGGER
        if not frame.is_ack:
            print(f"[Data Link Layer] {receiver.name} sending actual ACK frame for Seq {frame.seq_num}")
            # ACK frame wapas bhej rahe hain taaki Switch receiver ka MAC seekh le
            self.send_ack(receiver, frame.source_mac, frame.seq_num)
        else:
            print(f"[Data Link Layer] ACK {frame.seq_num} received successfully.")

        self.received_frames += 1

    def add_error_detection(self, frame):
        frame.error_code = sum(ord(c) for c in frame.payload) % 256

    def check_error(self, frame):
        calculated = sum(ord(c) for c in frame.payload) % 256
        return calculated == frame.error_code

    def send_ack(self, sender, receiver_mac, seq_num):
    # sender: Jo device ACK bhej raha hai (e.g., riyanshi)
    # receiver_mac: Jise ACK milna chahiye (Original Sender ka MAC, e.g., bhumika)
        print(f"\n[Data Link Layer] {sender.name} is sending ACK for Seq {seq_num}")
    
    # 1. ACK Frame banao (Source = sender, Dest = original sender's MAC)
        ack_frame = Frame(sender.mac_address, receiver_mac, "ACK")
        ack_frame.is_ack = True
        ack_frame.seq_num = seq_num

    # 2. Intermediate device (Switch/Hub) dhundo jo sender se connected hai
        connected_device = next((p for p in sender.ports if isinstance(p, (Hub, Switch, Bridge))), None)

    # 3. ACK ko Switch/Hub ke through bhejo taaki learning ho
        if isinstance(connected_device, Switch):
        # Switch 'sender' (riyanshi) ka MAC learn karega aur ACK forward karega
            connected_device.forward(sender, ack_frame, self)
        elif isinstance(connected_device, Hub):
            connected_device.broadcast(sender, ack_frame, self)
        else:
        # Agar koi intermediate device nahi hai, toh direct bhej do
            receiver_device = self.mac_table.get(receiver_mac)
            if receiver_device:
                self.physical_layer.transmit(sender, receiver_device, ack_frame, self)
            else:
                print("[Data Link Layer] ERROR: Receiver device not found for ACK!")

    def stats(self):
        print("\n--- Data Link Layer Stats ---")
        print(f"Frames Sent: {self.sent_frames}")
        print(f"Frames Received: {self.received_frames}")