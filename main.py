from core import SimulatorCore, Frame, Device, Hub, Switch
from phy_layer import PhysicalLayer
from datalink import DataLinkLayer
from protocols import CSMACD, GoBackN, ChecksumProtocol

def main():
    sim = SimulatorCore()
    phy = PhysicalLayer()
    dll = DataLinkLayer(phy)
    csma = CSMACD()
    gbn = GoBackN(phy, dll)
    checksum = ChecksumProtocol()

    dll.set_access_protocol(csma)
    dll.set_flow_control_protocol(gbn)

    print("--- Network Simulator ---")
    
    # 1. Choose Topology
    print("\nSelect Topology to build:")
    print("1. Point-to-Point (2 Devices)")
    print("2. Star Topology (N Devices + 1 Hub)")
    print("3. Switch Topology (N Devices + 1 Switch)")
    print("4. Star topology (N device + 2 hubs + 1 switch)")
    choice = input("Enter choice: ")

    if choice == "1":
        # Create Point-to-Point
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
    
    elif choice == "3":
       # Create Star Topology (Switch)
        sw_name = input("Enter Switch name: ")
        star_switch = Switch(sw_name)
        sim.add_device(star_switch)
        
        num = int(input("How many devices? "))
        for i in range(num):
            pc = Device(input(f"Device {i+1} name: "))
            sim.add_device(pc)
            pc.connect(star_switch)

    elif choice == "4":
        # Create two star topologies connected by a switch 
        sw_name = input("Enter central Switch name: ")
        main_switch = Switch(sw_name)
        sim.add_device(main_switch)
 
        hub1 = Hub("Hub1")
        hub2 = Hub("Hub2")
        sim.add_device(hub1)
        sim.add_device(hub2)

        main_switch.connect(hub1)
        main_switch.connect(hub2)

        # Connect 5 devices to Hub 1 
        print("\nConnecting 5 devices to Hub 1...")
        for i in range(5):
            pc = Device(f"H1_PC{i+1}")
            sim.add_device(pc)
            pc.connect(hub1)

        # Connect 5 devices to Hub 2 
        print("\nConnecting 5 devices to Hub 2...")
        for i in range(5):
            pc = Device(f"H2_PC{i+1}")
            sim.add_device(pc)
            pc.connect(hub2)

    # 2. Select Sender and Receiver
    print("\n--- Available Devices ---")
    for name in sim.all_devices:
        print(f"- {name}")

    sender_name = input("\nEnter Sender name: ")
    receiver_name = input("Enter Receiver name: ")
    message = input("Enter message to send: ")

    sender = sim.all_devices.get(sender_name)
    receiver = sim.all_devices.get(receiver_name)

    # 3. Execute Transmission 
    if sender and receiver:
        dll.send(sender, receiver, message) 
        sim.get_stats()
    else:
        print("Device not available")

if __name__ == "__main__":
    main()