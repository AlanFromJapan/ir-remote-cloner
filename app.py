#!/usr/bin/env python3
"""
IR Remote Cloner - Command Line Application
Connects to a serial device to capture IR remote codes and stores them in SQLite database.
"""

import time
import sys
import select
import termios
import tty
import argparse
from typing import Optional
from db import Database
from terminal_colors import terminal_colors
from codegen import generate_arduino_code



# Try to import serial, handle gracefully if not available
try:
    import serial
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False
    print("Warning: pyserial not installed. Serial functionality will be limited.")
    print("Install with: pip install pyserial")






class SerialHandler:
    """Handles serial communication"""
    
    def __init__(self, port: str = "/dev/ttyUSB0", baudrate: int = 9600):
        self.port = port
        self.baudrate = baudrate
        self.connection = None
    
    def connect(self) -> bool:
        """Connect to serial port"""
        if not SERIAL_AVAILABLE:
            return False
        
        try:
            self.connection = serial.Serial(self.port, self.baudrate, timeout=0.1)
            return True
        except (serial.SerialException, FileNotFoundError):
            return False
    
    def disconnect(self):
        """Disconnect from serial port"""
        if self.connection and self.connection.is_open:
            self.connection.close()
    
    def read_line(self) -> Optional[str]:
        """Read a line from serial port"""
        if not self.connection or not self.connection.is_open:
            return None
        
        try:
            if self.connection.in_waiting > 0:
                line = self.connection.readline().decode('utf-8').strip()
                return line if line else None
        except (serial.SerialException, UnicodeDecodeError):
            pass
        
        return None
    
    def is_connected(self) -> bool:
        """Check if serial is connected"""
        return self.connection and self.connection.is_open

    def flush_input(self):
        """Flush input buffer"""
        if self.connection and self.connection.is_open:
            self.connection.reset_input_buffer()


class InputHandler:
    """Handles keyboard input"""
    
    @staticmethod
    def get_char():
        """Get a single character from stdin"""
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch
    
    @staticmethod
    def check_escape() -> bool:
        """Check if ESC key was pressed (non-blocking)"""
        if select.select([sys.stdin], [], [], 0)[0]:
            ch = InputHandler.get_char()
            return ch == '\x1b'  # ESC key
        return False


class IRRemoteCloner:
    """Main application class"""
    
    def __init__(self, serial_port: str = None, baudrate: int = 9600):
        self.db = Database()
        self.serial_handler = SerialHandler(port=serial_port if serial_port else "/dev/ttyUSB0", baudrate=baudrate)
    
    def print_header(self):
        """Print application header"""
        print("\n" + "="*50)
        print("IR Remote Cloner")
        print("="*50)
    
    def print_menu(self):
        """Print main menu"""
        print(terminal_colors.HEADER + "\nWhat would you like to do?" + terminal_colors.ENDC)
        print("1 - Create a new remote")
        print("2 - List remotes")
        print("3 - Register new keys")
        print("4 - View registered keys")
        print("5 - Read serial data (debug)")
        print("6 - Generate Arduino code")
        print("7 - Send code to Arduino")
        print(terminal_colors.FAIL + "q - Quit" + terminal_colors.ENDC)
        print()
    
    def create_new_remote(self):
        """Handle creating a new remote"""
        print("\n--- Create New Remote ---")
        
        name = input("Enter remote name (empty to cancel): ").strip()
        if not name:
            print("Cancelled creating new remote.")
            return
        
        comment = input("Enter comment (optional): ").strip()
        comment = comment if comment else None
        
        try:
            remote_id = self.db.create_remote(name, comment)
            print(f"Remote '{name}' created successfully with ID: {remote_id}")
        except ValueError as e:
            print(f"Error: {e}")
    
    def list_remotes(self):
        """Handle listing remotes"""
        print("\n--- Remote List ---")
        
        remotes = self.db.list_remotes()
        
        if not remotes:
            print("No remotes found.")
            return
        
        print(f"{'ID':<5} {'Name':<20} {'Comment'}")
        print("-" * 50)
        
        for remote_id, name, comment in remotes:
            comment_display = comment if comment else ""
            print(f"{remote_id:<5} {name:<20} {comment_display}")
    
    def register_new_keys(self):
        """Handle registering new keys"""
        print("\n--- Register New Keys ---")
        
        # Show available remotes
        remotes = self.db.list_remotes()
        if not remotes:
            print("No remotes found. Please create a remote first.")
            return
        
        print("Available remotes:")
        for remote_id, name, comment in remotes:
            print(f"  {remote_id}: {name}")
        
        # Get remote ID
        try:
            remote_id = int(input("\nEnter remote ID: "))
            remote = self.db.get_remote(remote_id)
            if not remote:
                print("Error: Invalid remote ID")
                return
        except ValueError:
            print("Error: Invalid remote ID")
            return
        
        print(f"Selected remote: {remote[1]}")
        print("\nPress ESC to exit key registration mode")
        
        # Try to connect to serial
        if SERIAL_AVAILABLE:
            if not self.serial_handler.connect():
                print(f"Warning: Could not connect to serial port {self.serial_handler.port}")
                print("Exiting key registration mode.")
                return
        
        
        # Main key registration loop

        print(terminal_colors.HEADER + "Waiting for IR codes... (Press ESC to exit)" + terminal_colors.ENDC)
        while True:
            # Check for ESC key
            if InputHandler.check_escape():
                print(terminal_colors.FAIL + "\nExiting key registration mode" + terminal_colors.ENDC)
                break
            
            # Check for serial data
            line = None
            if self.serial_handler.is_connected():
                line = self.serial_handler.read_line()
            
            if line:
                #print the line
                print(terminal_colors.SERIAL_DATA + f"(INPUT)   :{line}" + terminal_colors.ENDC) 

                while True:
                    #purge any extra data
                    time.sleep(0.2)            
                    purge = self.serial_handler.read_line()
                    if not purge:
                        break
                    else:
                        print(terminal_colors.SERIAL_DATA + f"(ignored) :{purge}" + terminal_colors.ENDC)


                # Parse the received data
                try:
                    register = False
                    parts = line.split(';')
                    if len(parts) <= 3:
                        print(terminal_colors.FAIL + f"Invalid data format: {line} need at least 3 parts separated by ';'" + terminal_colors.ENDC)
                    else:
                        register = True
                    
                    if register:
                        protocol, addr, command = parts[0:3]
                        print(f"Received: Protocol={protocol}, Address={addr}, Command={command}")
                        
                        # Get key name
                        key_name = None
                        while not key_name:
                            key_name = input("Enter key name or empty to cancel: ").strip()
                            if not key_name or key_name == '':
                                break
                        
                        if key_name == '':
                            print(terminal_colors.FAIL + "Key registration cancelled for this code." + terminal_colors.ENDC)
                            register = False
                        
                        if register:
                            # Get optional comment
                            comment = input("Enter comment (optional): ").strip()
                            comment = comment if comment else None
                            
                            # Save to database
                            self.db.add_key(remote_id, protocol, addr, command, key_name, comment)
                            print(terminal_colors.OKBLUE + f"Key '{key_name}' saved successfully" + terminal_colors.ENDC)
                    
                except Exception as e:
                    print(f"Error saving key: {e}")

                print(terminal_colors.HEADER + "Waiting for IR codes... (Press ESC to exit)" + terminal_colors.ENDC)


        # Cleanup
        self.serial_handler.disconnect()
    

    def debug_show_serial(self):
        """Handle debug serial data reading"""
        print("\n--- (DEBUG) Show serial data ---")
        
        # Try to connect to serial
        if SERIAL_AVAILABLE:
            if not self.serial_handler.connect():
                print(f"Warning: Could not connect to serial port {self.serial_handler.port}")
                return
            
        print(terminal_colors.HEADER + "Waiting for IR codes... (Press ESC to exit)" + terminal_colors.ENDC)
        while True:
            # Check for ESC key
            if InputHandler.check_escape():
                print(terminal_colors.FAIL + "\nExiting debug view" + terminal_colors.ENDC)
                break
            
            # Check for serial data
            line = None
            if self.serial_handler.is_connected():
                while True:
                    line = self.serial_handler.read_line()
                    if not line:
                        break
                    print(terminal_colors.SERIAL_DATA + f"{line}" + terminal_colors.ENDC) 
                    time.sleep(0.2)            

        # Cleanup
        self.serial_handler.disconnect()



    def view_registered_keys(self):
        """Handle viewing registered keys for a remote"""
        print("\n--- View Registered Keys ---")
        
        # Show available remotes
        remotes = self.db.list_remotes()
        if not remotes:
            print("No remotes found. Please create a remote first.")
            return -1
        
        print("Available remotes:")
        for remote_id, name, comment in remotes:
            print(f"  {remote_id}: {name}")
        
        # Get remote ID
        try:
            remote_id = int(input("\nEnter remote ID: "))
            remote = self.db.get_remote(remote_id)
            if not remote:
                print("Error: Invalid remote ID")
                return -1
        except ValueError:
            print("Error: Invalid remote ID")
            return -1
        
        print(f"\nRegistered keys for remote: {remote[1]}")
        
        # Get keys for this remote
        keys = self.db.get_keys_for_remote(remote_id)
        
        if not keys:
            print("No keys registered for this remote.")
            return -1
        
        # Display keys in a table format
        print("\n" + "-" * 80)
        print(f"{'Key Name':<15} {'Protocol':<12} {'Address':<10} {'Command':<10} {'Comment':<20}")
        print("-" * 80)
        
        for key_name, protocol, address, command, comment in keys:
            comment_display = comment if comment else ""
            print(f"{key_name:<15} {protocol:<12} {address:<10} {command:<10} {comment_display:<20}")
        
        print("-" * 80)
        print(f"Total keys: {len(keys)}")
    
        return remote_id


    def send_code_to_arduino(self):
        # Sends code to the arduino via serial. This is a placeholder for future implementation.
        print(terminal_colors.OKGREEN + ">> First, pick a remote and code to generate send." + terminal_colors.ENDC)
        remote_id = self.view_registered_keys()
        if remote_id <= -1:
            return
        
        try:      
            print (terminal_colors.OKGREEN + ">> Enter key name to send or empty to cancel:" + terminal_colors.ENDC)      
            keyname = input("\nEnter key name (case insensitive): ").strip()
            if not keyname:
                print("Cancelled sending code.")
                return            

            keys = self.db.get_keys_for_remote(remote_id)
            key_found = [k for k in keys if k[0].lower() == keyname.lower()]
            if not key_found:
                print(terminal_colors.FAIL + f"Error: Key '{keyname}' not found for this remote." + terminal_colors.ENDC)
                return

            key_tuple = key_found[0]

            print(f">> Sending code for key '{keyname}' [{key_tuple}] to Arduino..." )

            print(terminal_colors.WARNING + "Now turn the Arduino in receiver mode and press [Enter] to send the code." + terminal_colors.ENDC)
            input()

            # Try to connect to serial
            if SERIAL_AVAILABLE:
                if not self.serial_handler.connect():
                    print(f"Warning: Could not connect to serial port {self.serial_handler.port}")
                    return            
                # Send the code in a simple format: address|command
                code_str = f"{key_tuple[2]}|{key_tuple[3]}\n"  # address|command
                self.serial_handler.connection.write(code_str.encode('ascii'))
                print ("> Code sent: " + code_str)

            else:
                print(terminal_colors.FAIL + "Serial functionality not available. Please install pyserial." + terminal_colors.ENDC)
                return

        except ValueError:
            print("Error: Invalid remote ID")
            return


    def run(self):
        """Main application loop"""
        try:
            while True:
                self.print_header()
                self.print_menu()
                
                choice = input("Enter your choice: ").strip().lower()
                
                if choice == '1':
                    self.create_new_remote()
                elif choice == '2':
                    self.list_remotes()
                elif choice == '3':
                    self.register_new_keys()
                elif choice == '4':
                    self.view_registered_keys()
                elif choice == '5':
                    self.debug_show_serial()
                elif choice == '6':
                    self.generate_arduino_code()
                elif choice == '7':
                    self.send_code_to_arduino()
                elif choice == 'q':
                    print("\nGoodbye!")
                    break
                else:
                    print("Invalid choice. Please try again.")
                
                input("\nPress Enter to continue...")
        
        except KeyboardInterrupt:
            print("\n\nApplication interrupted by user")
        except Exception as e:
            print(f"\nUnexpected error: {e}")
        finally:
            self.serial_handler.disconnect()


    def generate_arduino_code(self):
        """Generate Arduino code for a selected remote"""
        print("\n--- Generate Arduino Code ---")
        
        # Show available remotes
        remotes = self.db.list_remotes()
        if not remotes:
            print("No remotes found. Please create a remote first.")
            return
        
        print("Available remotes:")
        for remote_id, name, comment in remotes:
            print(f"  {remote_id}: {name}")
        
        # Get remote ID
        try:
            remote_id = int(input("\nEnter remote ID: "))
            remote = self.db.get_remote(remote_id)
            if not remote:
                print("Error: Invalid remote ID")
                return
        except ValueError:
            print("Error: Invalid remote ID")
            return
        
        # Generate Arduino code
        generate_arduino_code(remote_id)


def main():
    """Entry point"""
    parser = argparse.ArgumentParser(description='IR Remote Cloner - Capture and store IR remote codes')
    parser.add_argument('--port', '-p', 
                       default='/dev/ttyACM1',
                       help='Serial port to connect to (default: /dev/ttyACM1)')
    parser.add_argument('--baudrate', '-b', 
                       default='115200',
                       help='Baud rate for serial communication (default: 115200)')    
    
    args = parser.parse_args()
    
    app = IRRemoteCloner(serial_port=args.port, baudrate=args.baudrate)
    app.run()


if __name__ == "__main__":
    main()
