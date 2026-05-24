# apps.py

class FTPServer:
    """Simulates a mini FTP Server handling basic file requests"""
    def __init__(self):
        # Mock files available on server
        self.file_directory = {
            "notes.txt": "Network Simulator Project Submission 3 Data.",
            "code.py": "print('Hello World from Mock FTP Server!')"
        }

    def handle_request(self, command):
        """Processes FTP commands like GET filename"""
        print(f"\n[FTP Server] Processing request: '{command}'")
        if command.startswith("GET "):
            filename = command.split(" ")[1]
            if filename in self.file_directory:
                return f"FTP_SUCCESS|File Data: {self.file_directory[filename]}"
            else:
                return "FTP_ERROR|File Not Found!"
        return "FTP_ERROR|Invalid FTP Command. Use 'GET <filename>'"


class TelnetServer:
    """Simulates a mini Telnet Server executing remote commands"""
    def __init__(self):
        pass

    def handle_request(self, command):
        """Processes remote terminal commands"""
        print(f"\n[Telnet Server] Executing remote terminal command: '{command}'")
        cmd = command.strip().lower()
        if cmd == "ping":
            return "TELNET_REPLY|Pong! Connection is alive."
        elif cmd == "help":
            return "TELNET_REPLY|Available commands: ping, help, exit"
        elif cmd == "exit":
            return "TELNET_REPLY|Closing remote terminal session."
        else:
            return f"TELNET_REPLY|'{command}' is not recognized as an internal command."