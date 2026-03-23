from core import Frame, Hub

class DataLinkLayer:
    def __init__(self, physical_layer):
        self.physical_layer = physical_layer

        # Placeholders for protocols (to be injected later)
        self.access_protocol = None
        self.flow_control_protocol = None

        # For stats / debugging
        self.sent_frames = 0
        self.received_frames = 0


    # CONFIGURATION METHODS
   
    def set_access_protocol(self, protocol):
        self.access_protocol = protocol

    def set_flow_control_protocol(self, protocol):
        self.flow_control_protocol = protocol


    # SENDER SIDE
  
    def send(self, sender, receiver, message):
        print("\n[Data Link Layer] Preparing frame...")

        frame = Frame(sender.mac_address, receiver.mac_address, message)

        # Step 1: Error Detection
        self.add_error_detection(frame)

        # Step 2: Check for Hub connection
        connected_hub = next((p for p in sender.ports if isinstance(p, Hub)), None)

        # Step 3: Access Control (HOOK)
        if self.access_protocol:
            print("[Data Link Layer] Using Access Control Protocol...")
            self.access_protocol.handle_access(sender, receiver, frame, self.physical_layer)

        else:
            if connected_hub:
                print("[Data Link Layer] Sending via Hub...")
                connected_hub.broadcast(sender, frame, self.physical_layer)
            else:
                print("[Data Link Layer] Direct transmission (Point-to-Point)")
                self.physical_layer.transmit(sender, receiver, frame)

        self.sent_frames += 1


    
    # RECEIVER SIDE
   
    def receive(self, receiver, frame):
        print(f"\n[Data Link Layer] {receiver.name} receiving frame...")

        # Error Check
        if not self.check_error(frame):
            print("[Data Link Layer] Error detected! Frame discarded.")
            return

        print("[Data Link Layer] Frame is error-free")

        # Flow Control (HOOK)
        if self.flow_control_protocol:
            print("[Data Link Layer] Handling Flow Control...")
            self.flow_control_protocol.handle_receive(receiver, frame)
        else:
            print("[Data Link Layer] No Flow Control → Delivering directly")

        print(f"[Data Link Layer] Data Delivered: {frame.payload}")

        self.received_frames += 1


    
    # ERROR DETECTION
    
    def add_error_detection(self, frame):
        frame.error_code = sum(ord(c) for c in frame.payload) % 256
        print(f"[Data Link Layer] Added Error Code: {frame.error_code}")

    def check_error(self, frame):
        calculated = sum(ord(c) for c in frame.payload) % 256
        return calculated == frame.error_code



    # FLOW CONTROL SUPPORT
   
    def send_ack(self, sender, receiver, seq_num):
        ack_frame = Frame(sender.mac_address, receiver.mac_address, "ACK")
        ack_frame.is_ack = True
        ack_frame.seq_num = seq_num

        print(f"[Data Link Layer] Sending ACK for Seq {seq_num}")
        self.physical_layer.transmit(sender, receiver, ack_frame)


    
    # DEBUG / STATS
    
    def stats(self):
        print("\n--- Data Link Layer Stats ---")
        print(f"Frames Sent: {self.sent_frames}")
        print(f"Frames Received: {self.received_frames}")