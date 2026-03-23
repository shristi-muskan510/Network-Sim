from core import Frame, Hub, Switch, Bridge

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
        print(f"\n[Data Link Layer] Splitting message: '{message}'")

        # Create a list of frames, one for each character 
        frames = []
        for char in message:
            # Create a frame with the character as payload [cite: 3]
            f = Frame(sender.mac_address, receiver.mac_address, char)
            
            # Step 1: Add Error Detection to EACH frame 
            self.add_error_detection(f)
            frames.append(f)

        # Step 2: Identify the intermediate device (Hub, Switch, or Bridge) [cite: 9, 19]
        connected_device = next((p for p in sender.ports if isinstance(p, (Hub, Switch, Bridge))), None)

        # Step 3: Handle Flow Control (Sliding Window) 
        if self.flow_control_protocol and len(frames) > 1:
            print(f"[Data Link Layer] Handing {len(frames)} frames to Flow Control Protocol...")
            
            # CHANGE: Pass the 'connected_device' (the Switch) as the target, not 'receiver'
            # If no switch exists, fall back to the receiver
            target = connected_device if connected_device else receiver
            
            self.flow_control_protocol.send(sender, target, frames)
            self.sent_frames += len(frames)
            return

        # Step 4: Handle Access Control or Direct Send if only 1 frame or no Flow Control
        for frame in frames:
            if self.access_protocol and connected_device:
                # Passes the frame through CSMA/CD logic [cite: 22, 26]
                self.access_protocol.handle_access(sender, connected_device, frame, self.physical_layer)
            elif isinstance(connected_device, Switch):
                connected_device.forward(sender, frame, self) # [cite: 19]
            elif isinstance(connected_device, Hub):
                connected_device.broadcast(sender, frame, self) # [cite: 15]
            else:
                self.physical_layer.transmit(sender, receiver, frame) # [cite: 12]
            
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