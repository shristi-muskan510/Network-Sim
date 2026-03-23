import random
import time

class CSMACD:
    def __init__(self):
        self.channel_busy = False

    def handle_access(self, sender, hub, frame, phy):
        attempt = 0
        while attempt < 10:
            print(f"\n{sender.name} sensing medium...")
            if self.channel_busy:
                time.sleep(1)
                continue
            
            self.channel_busy = True
            if random.random() < 0.5: # Collision simulation
                print("Collision! Backing off...")
                self.channel_busy = False
                time.sleep(random.randint(1, 3))
                attempt += 1
                continue

            print("Success! Transmitting.")
            if hasattr(hub, 'broadcast'):
                hub.broadcast(sender, frame, phy)
            elif hasattr(hub, 'forward'):
                hub.forward(sender, frame, phy)
            self.channel_busy = False
            return

class GoBackN:
    def __init__(self, phy_layer, datalink_layer):
        self.phy = phy_layer
        self.dll = datalink_layer

    def send(self, sender, receiver, frames, window_size=4):
        first_outstanding = 0
        next_seq = 0

        while first_outstanding < len(frames):
            # Window Transmission
            while next_seq < first_outstanding + window_size and next_seq < len(frames):
                frame = frames[next_seq]
                frame.seq_num = next_seq
                print(f"[GBN] Sending Frame {frame.seq_num}")
                
                if hasattr(receiver, 'forward'):
                    receiver.forward(sender, frame, self.dll)
                elif hasattr(receiver, 'broadcast'):
                    receiver.broadcast(sender, frame, self.dll)
                else:
                    self.phy.transmit(sender, receiver, frame)
                next_seq += 1

            # Simulation of waiting for actual ACKs
            print(f"[GBN] Waiting for receiver to process and Switch to learn...")
            time.sleep(1) 
            
            # Yahan hum maan rahe hain ki ACKs mil gaye (Progress)
            first_outstanding = next_seq

# ... ChecksumProtocol class as it is ...
    
class ChecksumProtocol:

    def __init__(self, bits=8):
        self.bits = bits
        self.modulo = 2 ** bits
        self.max_val = self.modulo - 1

    def generate(self, data):
        """
        data: string ya list dono handle karega
        """

        # Convert to numeric list if string
        if isinstance(data, str):
            data_list = [ord(c) for c in data]
        else:
            data_list = data

        total_sum = sum(data_list)

        # Wrap using modulo (dynamic)
        wrapped_sum = total_sum % self.modulo

        # 1's complement
        checksum = self.max_val - wrapped_sum

        print(f"[Checksum Sender] Sum: {total_sum}, Wrapped: {wrapped_sum}, Checksum: {checksum}")
        return checksum

    def verify(self, data, received_checksum):
        """
        Verify checksum
        """

        if isinstance(data, str):
            data_list = [ord(c) for c in data]
        else:
            data_list = data

        total_sum = sum(data_list) + received_checksum

        wrapped_sum = total_sum % self.modulo

        check = self.max_val - wrapped_sum

        if check == 0:
            print("[Checksum Receiver] Check Passed! No error.")
            return True
        else:
            print("[Checksum Receiver] Check Failed! Error detected.")
            return False