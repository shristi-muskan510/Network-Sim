from core import SimulatorCore, Frame, Device, Hub, Switch
from phy_layer import PhysicalLayer
from datalink import DataLinkLayer
from protocols import CSMACD, GoBackN, ChecksumProtocol

# ---RIYANSHI---
from core import SimulatorCore, Frame, Device, Hub, Switch, Router # Naya: Router add kiya
from network_utils import is_valid_ipv4, get_network_address       # Naya: Validation import kiya
from network import NetworkLayer


def main():
    sim = SimulatorCore()
    phy = PhysicalLayer()
    dll = DataLinkLayer(phy)
    nl = NetworkLayer(dll) # Connected main to network.py
    
    csma = CSMACD(dll)
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
    print("6. Complex Topology (4 Routers + RIP Dynamic Routing)")

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

    elif choice == "6":
        print("\n--- Building Complex Topology (3 Routers, 2 Switches) ---")
        # Create Routers
        r0 = Router("R0")
        r1 = Router("R1")
        r2 = Router("R2")
        for r in [r0, r1, r2]:
            sim.add_device(r)

        # Create Switches
        sw0 = Switch("SW0")
        sw1 = Switch("SW1")
        sim.add_device(sw0)
        sim.add_device(sw1)

        # Connect Switches to Routers
        r0.configure_interface(0, "10.0.0.1", "255.255.255.0", sw0)
        r2.configure_interface(0, "10.0.1.1", "255.255.255.0", sw1)

        # Create PCs for SW0
        pc0_1 = Device("PC0_1")
        pc0_1.ip_address = "10.0.0.10"
        pc0_1.subnet_mask = "255.255.255.0"
        pc0_2 = Device("PC0_2")
        pc0_2.ip_address = "10.0.0.11"
        pc0_2.subnet_mask = "255.255.255.0"
        for pc in [pc0_1, pc0_2]:
            sim.add_device(pc)
            pc.connect(sw0)

        # Create PCs for SW1
        pc1_1 = Device("PC1_1")
        pc1_1.ip_address = "10.0.1.10"
        pc1_1.subnet_mask = "255.255.255.0"
        pc1_2 = Device("PC1_2")
        pc1_2.ip_address = "10.0.1.11"
        pc1_2.subnet_mask = "255.255.255.0"
        for pc in [pc1_1, pc1_2]:
            sim.add_device(pc)
            pc.connect(sw1)

        # Connect Routers (Triangle R0-R1-R2)
        r0.configure_interface(1, "192.168.1.1", "255.255.255.0", r1)
        r1.configure_interface(0, "192.168.1.2", "255.255.255.0", r0)

        r1.configure_interface(1, "192.168.2.1", "255.255.255.0", r2)
        r2.configure_interface(1, "192.168.2.2", "255.255.255.0", r1)

        r2.configure_interface(2, "192.168.3.1", "255.255.255.0", r0)
        r0.configure_interface(2, "192.168.3.2", "255.255.255.0", r2)

        # Initialize Dynamic Routing
        from routing import RIPRoutingEngine
        print("\n--- Starting Dynamic Routing (RIP) ---")
        print("RIP Convergence logs are being saved to 'rip.log'...")
        rip_engines = []
        for r in [r0, r1, r2]:
            rip = RIPRoutingEngine(r)
            rip.initialize_local_routes()
            rip_engines.append(rip)
        
        # Simulate convergence and save to rip.log
        import sys, os
        old_stdout = sys.stdout
        with open("rip.log", "w") as rip_log:
            sys.stdout = rip_log
            for cycle in range(3):
                for rip in rip_engines:
                    rip.send_rip_updates(dll)
        sys.stdout = old_stdout
        print("--- RIP Convergence Complete! ---")

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
        print(f"\n[Short] {sender.name} is sending '{message}' to {receiver.name}...")
        print("Full detailed simulation logs are being saved to 'simulation.log'...")
        
        with open("simulation.log", "w") as sim_log:
            sys.stdout = sim_log
            nl.send(sender, receiver, message) 
            
        sys.stdout = old_stdout
        print(f"[Short] '{message}' successfully received by {receiver.name} with all ACKs!")
        sim.get_stats()
    else:
        print("Device not available")

if __name__ == "__main__":
    main()