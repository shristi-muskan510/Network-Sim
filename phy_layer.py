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

    def transmit(self, sender, receiver, frame,dll=None): # fun to send data from sender to receiver
        print(f"\n[Physical Layer] Transmitting from {sender.name} to {receiver.name}")

        bits = self.encode(frame) #convert encoded data into bits

        print("[Physical Layer] Sending bits...")

        # Direct simulation
        self.receive(receiver, bits, frame,dll) #pass data to receiver directly 

    # phy_layer.py mein update karein
    def receive(self, receiver, bits, frame, dll=None):
        print(f"\n[Physical Layer] {receiver.name} Receiving bits...")

    # Preamble Check (Standard logic from your file)
        expected_preamble = "10101010"
        received_preamble = bits[:8]
        if received_preamble != expected_preamble:
            print("❌ [Physical Layer] Invalid Preamble!")
            return None

    # MAC Check (Standard logic)
        if receiver.mac_address != frame.dest_mac:
            print(f"❌ [Physical Layer] Frame not for {receiver.name}. Discarded.")
            return None

        # Decoding Logic
        data_bits = bits[8:]
        data = "".join(chr(int(data_bits[i:i+8], 2)) for i in range(0, len(data_bits), 8))
        print(f"[Physical Layer] Decoded Data: {data}")

        # DLL Trigger (The "All Good" part)
        if dll:
            dll.receive(receiver, frame) 
    
        return data