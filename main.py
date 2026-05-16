from core import SimulatorCore, Frame, Device, Hub, Switch
from phy_layer import PhysicalLayer
from datalink import DataLinkLayer
from protocols import CSMACD, GoBackN, ChecksumProtocol

# ---RIYANSHI---
from core import SimulatorCore, Frame, Device, Hub, Switch, Router # Naya: Router add kiya
from network_utils import is_valid_ipv4, get_network_address       # Naya: Validation import kiya


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

    #---RIYANSHI---
    print("5. Routed Subnet Topology (2 Subnets + 1 Router) - Part 2") # NAYA OPTION

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
    

    #---RIYANSHI: logic for new option -> option 5---
    
    elif choice == "5":
        # --- PERSON 2: Setting up Identities & Topology Mapping ---
        r_name = input("Enter Router Name: ")
        router = Router(r_name)
        sim.add_device(router)

        # ---- SUBNET 1 SETUP (e.g., 192.168.1.0/24) ----
        print("\n--- Configuring Subnet 1 ---")
        pc1_name = input("Enter name for PC1: ")
        pc1 = Device(pc1_name)
        
        # IP Validation Loop
        while True:
            ip = input(f"Assign valid IP for {pc1_name} (e.g., 192.168.1.10): ")
            if is_valid_ipv4(ip):
                pc1.ip_address = ip
                pc1.subnet_mask = "255.255.255.0"
                break
            print("❌ Invalid IP address format! Try again (0-255 per octet).")
            
        sim.add_device(pc1)
        # Router ke Interface 0 ko PC1 (Subnet 1) se jodo
        router.configure_interface(0, "192.168.1.1", "255.255.255.0", pc1)

        # ---- SUBNET 2 SETUP (e.g., 192.168.2.0/24) ----
        print("\n--- Configuring Subnet 2 ---")
        pc2_name = input("Enter name for PC2: ")
        pc2 = Device(pc2_name)
        
        while True:
            ip = input(f"Assign valid IP for {pc2_name} (e.g., 192.168.2.10): ")
            if is_valid_ipv4(ip):
                pc2.ip_address = ip
                pc2.subnet_mask = "255.255.255.0"
                break
            print("❌ Invalid IP address format! Try again.")
            
        sim.add_device(pc2)
        # Router ke Interface 1 ko PC2 (Subnet 2) se jodo
        router.configure_interface(1, "192.168.2.1", "255.255.255.0", pc2)

        # ---- STATIC ROUTING TABLE DEFINITION ----
        # Format: (Destination_Network, Subnet_Mask, Output_Interface_Port)
        # Tumne manually map bana kar router ko de diya
        router.routing_table = [
            ("192.168.1.0", "255.255.255.0", 0),
            ("192.168.2.0", "255.255.255.0", 1)
        ]
        print(f"\n[Static Routing] Table initialized on {router.name} for Subnet 1 & 2.")


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