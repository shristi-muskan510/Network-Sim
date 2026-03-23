class PhysicalLayer:
    def encode(self, frame):
        binary_data = ''.join(format(ord(c), '08b') for c in frame.payload)
        transmitted_bits = frame.preamble + binary_data
        print("\n[Physical Layer] Encoding...")
        print("Preamble:", frame.preamble)
        print("Binary Data:", binary_data)
        print("Transmitted Bits:", transmitted_bits)
        return transmitted_bits

    def transmit(self, sender, receiver, frame, datalink_layer): 
        # Added datalink_layer to fix TypeError
        print(f"\n[Physical Layer] Transmitting from {sender.name} to {receiver.name}")
        bits = self.encode(frame)
        print("[Physical Layer] Sending bits...")
        
        # FIX: Pass 'sender' so 'receive' knows where the bits came from
        self.receive(receiver, bits, frame, datalink_layer, sender)

    def receive(self, receiver, bits, frame, datalink_layer, original_sender):
        # Local import to prevent circular dependency
        from core import Hub, Switch, Bridge

        print(f"\n[Physical Layer] {receiver.name} Receiving bits...")

        # 1. Check preamble
        expected_preamble = "10101010"
        received_preamble = bits[:8]

        if received_preamble != expected_preamble:
            print("❌ [Physical Layer] Invalid Preamble! Data Rejected.")
            return None
        
        # 2. Networking Device Logic
        if isinstance(receiver, (Hub, Switch, Bridge)):
            print(f"[Physical Layer] {receiver.name} is a networking device. Passing to Layer 2...")
            
            # CRITICAL FIX: Use 'original_sender' instead of 'receiver'
            # This ensures the Hub/Switch doesn't send the frame back to its source
            if isinstance(receiver, (Switch, Bridge)):
                receiver.forward(original_sender, frame, datalink_layer)
            elif isinstance(receiver, Hub):
                receiver.broadcast(original_sender, frame, datalink_layer)
            return

        # 3. End-Device MAC Check (Data Link Layer logic inside PHY for simulation simplicity)
        if receiver.mac_address != frame.dest_mac:
            print(f"❌ [Physical Layer] Frame not for {receiver.name}. Discarded.")
            return None

        # 4. Data Decoding
        data_bits = bits[8:]
        data = "".join(chr(int(data_bits[i:i+8], 2)) for i in range(0, len(data_bits), 8))

        if "error" in data.lower():
            print("❌ [Physical Layer] Corrupted Data! Rejected.")
            return None

        print("[Physical Layer] Decoded Data:", data)
        
        # Trigger DataLinkLayer receive logic for the actual target
        datalink_layer.receive(receiver, frame) 
        return data