from core import SimulatorCore, Frame, Device, Hub
from phy_layer import PhysicalLayer

def main():
    sim = SimulatorCore()
    phy = PhysicalLayer()

    print("--- Network Simulator ---")
    
    # 1. Choose Topology
    print("\nSelect Topology to build:")
    print("1. Point-to-Point (2 Devices)")
    print("2. Star Topology (N Devices + 1 Hub)")
    choice = input("Enter choice (1 or 2): ")

    if choice == "1":
        # Create Point-to-Point [cite: 12]
        name_a = input("Enter name for Device 1: ")
        name_b = input("Enter name for Device 2: ")
        dev_a = Device(name_a)
        dev_b = Device(name_b)
        sim.add_device(dev_a)
        sim.add_device(dev_b)
        dev_a.connect(dev_b) 

    elif choice == "2":
        # Create Star Topology 
        hub_name = input("Enter Hub name: ")
        star_hub = Hub(hub_name)
        sim.add_device(star_hub)
        
        num_devices = int(input("How many end devices to connect to the hub? "))
        for i in range(num_devices):
            name = input(f"Enter name for Device {i+1}: ")
            pc = Device(name)
            sim.add_device(pc)
            pc.connect(star_hub)

    # 2. Select Sender and Receiver
    print("\n--- Available Devices ---")
    for name in sim.all_devices:
        print(f"- {name}")

    sender_name = input("\nEnter Sender name: ")
    receiver_name = input("Enter Receiver name: ")
    message = input("Enter message to send: ")

    sender = sim.all_devices.get(sender_name)
    receiver = sim.all_devices.get(receiver_name)

    if sender and receiver:
        # 3. Execute Transmission 
        test_frame = Frame(sender.mac_address, receiver.mac_address, message)
        
        # Check if connected to a hub for "exact working principles" 
        # This part requires you to check if the sender is connected to a hub in its ports
        connected_hub = next((p for p in sender.ports if isinstance(p, Hub)), None)
        
        if connected_hub:
            connected_hub.broadcast(sender, test_frame, phy) 
        else:
            phy.transmit(sender, receiver, test_frame) 
        
        sim.get_stats()
    else:
        print("Device not available")

if __name__ == "__main__":
    main()