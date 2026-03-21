import random
import time

class CSMACD:

    def __init__(self):
        self.channel_busy = False

    def transmit(self, sender, hub, frame, phy):
        
        attempt = 0

        while attempt < 10:

            print(f"\n{sender.name} wants to send")

            # Step 1: Check channel
            if self.channel_busy:
                print("Channel busy → waiting")
                time.sleep(1)
                continue

            # Step 2: Start sending
            print("Channel free → sending...")
            self.channel_busy = True

            # Step 3: Collision (random)
            if random.random() < 0.5:
                print("Collision happened!")

                self.channel_busy = False

                # Step 4: Backoff
                wait = random.randint(1, 3)
                print(f"Waiting {wait} sec before retry")
                time.sleep(wait)

                attempt += 1
                continue

            # Step 5: Success
            print("No collision → success!")

            hub.broadcast(sender, frame, phy)

            self.channel_busy = False
            return

        print("Failed to send after many attempts")

class GoBackN:
    def __init__(self, phy_layer):
        self.phy = phy_layer

    def send(self, sender, receiver, frames, window_size=4):
        first_outstanding = 0
        next_seq = 0

        while first_outstanding < len(frames):

            # Send frames in window
            while next_seq < first_outstanding + window_size and next_seq < len(frames):
                frame = frames[next_seq]
                frame.seq_num = next_seq

                print(f"[GBN] Sending Frame {frame.seq_num}")
                self.phy.transmit(sender, receiver, frame)

                next_seq += 1

            print(f"[GBN] Waiting for ACK from frame {first_outstanding}...")
            time.sleep(0.5)

            # ACK simulation
            if random.random() < 0.8:
                ack_received = random.randint(first_outstanding, next_seq)
                print(f"[GBN] ACK received till {ack_received-1}")

                first_outstanding = ack_received

            else:
                print(f"[GBN] Timeout! Resending from {first_outstanding}")
                next_seq = first_outstanding

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