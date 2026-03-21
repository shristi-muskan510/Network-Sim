import random
from core import Frame, Device

# Data Link Layer for End Devices

class DataLinkDevice:
    def __init__(self, device, physical_layer):
        self.device = device
        self.physical_layer = physical_layer

        # Go-Back-N variables
        self.window_size = 4
        self.base = 0
        self.next_seq = 0
        self.sent_frames = {}

    #Checksum Functions
   
    def add_checksum(self, frame):
        frame.error_code = sum(ord(c) for c in frame.payload)

    def check_error(self, frame):
        return frame.error_code == sum(ord(c) for c in frame.payload)

    
    # CSMA/CD (Access Control)
   
    def channel_busy(self):
        # Simulate channel status
        return random.choice([True, False, False])  # less probability of busy

    def collision_detected(self):
        return random.choice([True, False, False, False])

   
    #  Send Single Frame
    
    def send(self, dest_mac, data):
        if self.next_seq >= self.base + self.window_size:
            print(f"[DLL] Window full. Cannot send now.")
            return

        frame = Frame(self.device.mac_address, dest_mac, data)
        frame.seq_num = self.next_seq
        frame.is_ack = False

        self.add_checksum(frame)

        print(f"[DLL] {self.device.name} sending Frame Seq={frame.seq_num}")

        # CSMA/CD
        if self.channel_busy():
            print(f"[DLL] Channel busy. {self.device.name} waits...")
            return

        # Send frame
        self._transmit_frame(frame)

        # Store for possible retransmission
        self.sent_frames[self.next_seq] = frame
        self.next_seq += 1

    
    #  Send Multiple Frames (Go-Back-N)
   
    def send_window(self, dest_mac, data_list):
        while self.next_seq < self.base + self.window_size and data_list:
            data = data_list.pop(0)

            frame = Frame(self.device.mac_address, dest_mac, data)
            frame.seq_num = self.next_seq
            frame.is_ack = False

            self.add_checksum(frame)

            print(f"[GBN] {self.device.name} sending Frame {frame.seq_num}")

            if self.channel_busy():
                print("[GBN] Channel busy, retry later")
                return

            self._transmit_frame(frame)

            self.sent_frames[self.next_seq] = frame
            self.next_seq += 1

    
    #  Retransmission (Go-Back-N)
  
    def retransmit_from(self, seq):
        print(f"[GBN] Retransmitting from Seq {seq}")

        for i in range(seq, self.next_seq):
            frame = self.sent_frames[i]
            print(f"[GBN] Resending Frame {i}")
            self._transmit_frame(frame)

   
    # Receive Frame
    
    def receive(self, frame):
        print(f"[DLL] {self.device.name} received Frame Seq={frame.seq_num}")

        # Simulate collision/error
        if self.collision_detected():
            print("[DLL] Collision/Error detected! Frame lost.")
            self.retransmit_from(self.base)
            return

        # Error detection
        if not self.check_error(frame):
            print("[DLL] Checksum failed! Discarding frame.")
            return

        # ACK handling
        if frame.is_ack:
            print(f"[DLL] ACK received for Seq {frame.ack_num}")
            self.base = frame.ack_num + 1
            return

        # Data received successfully
        print(f"[DLL] Data accepted: {frame.payload}")

        # Send ACK
        ack = Frame(self.device.mac_address, frame.source_mac, "")
        ack.is_ack = True
        ack.ack_num = frame.seq_num

        print(f"[DLL] Sending ACK for {frame.seq_num}")
        self._transmit_frame(ack)

    
    #  Internal Transmit Function
   
    def _transmit_frame(self, frame):
        for port in self.device.ports:
            self.physical_layer.transmit(self.device, port, frame)



#  Switch (Data Link Layer Device)

class Switch(Device):
    def __init__(self, name, physical_layer):
        super().__init__(name)
        self.mac_table = {}
        self.physical_layer = physical_layer

    def receive(self, sender, frame):
        print(f"[Switch {self.name}] Frame received from {sender.name}")

        # Learn MAC address
        self.mac_table[frame.source_mac] = sender

        # Forward logic
        if frame.dest_mac in self.mac_table:
            target = self.mac_table[frame.dest_mac]
            print(f"[Switch] Forwarding to {target.name}")
            self.physical_layer.transmit(self, target, frame)
        else:
            print("[Switch] Unknown MAC → Broadcasting")

            for device in self.ports:
                if device != sender:
                    self.physical_layer.transmit(self, device, frame)