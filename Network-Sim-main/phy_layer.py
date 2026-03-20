class PhysicalLayer:

    def encode(self, frame):
        # Convert data to binary
        binary_data = ''.join(format(ord(c), '08b') for c in frame.payload) #convert every char into 8-bit binary

        # Add preamble
        transmitted_bits = frame.preamble + binary_data # Preamble + data = final transmitted bits

        print("\n[Physical Layer] Encoding...")
        print("Preamble:", frame.preamble)
        print("Binary Data:", binary_data)
        print("Transmitted Bits:", transmitted_bits)

        return transmitted_bits

    def transmit(self, sender, receiver, frame): # fun to send data from sender to receiver
        print(f"\n[Physical Layer] Transmitting from {sender.name} to {receiver.name}")

        bits = self.encode(frame) #convert encoded data into bits

        print("[Physical Layer] Sending bits...")

        # Direct simulation
        self.receive(receiver, bits) #pass data to receiver directly 

    def receive(self, receiver, bits): # receiving bits on receiver side
        print(f"\n[Physical Layer] {receiver.name} Receiving bits...")

        # Remove preamble (first 8 bits)
        data_bits = bits[8:]

        # Convert binary to text
        # process every 8-bit chunk
        data = ""
        for i in range(0, len(data_bits), 8):
            byte = data_bits[i:i+8]
            data += chr(int(byte, 2)) #convert back binary into char 

        print("[Physical Layer] Decoded Data:", data)

        return data