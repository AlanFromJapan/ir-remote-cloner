#!/usr/bin/env python3
"""
IR Remote Cloner - Command Line Application
Connects to a serial device to capture IR remote codes and stores them in SQLite database.
"""

import sqlite3
import sys
import os
import select
import termios
import tty
import argparse
from typing import Optional, Tuple, List

# Try to import serial, handle gracefully if not available
try:
    import serial
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False
    print("Warning: pyserial not installed. Serial functionality will be limited.")
    print("Install with: pip install pyserial")


class Database:
    """Handles SQLite database operations"""
    
    def __init__(self, db_path: str = "ir_remotes.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create Remote table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Remote (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                comment TEXT
            )
        """)
        
        # Create Key table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Key (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                remote_id INTEGER NOT NULL,
                protocol TEXT NOT NULL,
                address TEXT NOT NULL,
                command TEXT NOT NULL,
                key_name TEXT NOT NULL,
                comment TEXT,
                FOREIGN KEY (remote_id) REFERENCES Remote (id),
                UNIQUE(remote_id, key_name)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def create_remote(self, name: str, comment: str = None) -> int:
        """Create a new remote and return its ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("INSERT INTO Remote (name, comment) VALUES (?, ?)", (name, comment))
            remote_id = cursor.lastrowid
            conn.commit()
            return remote_id
        except sqlite3.IntegrityError:
            raise ValueError(f"Remote with name '{name}' already exists")
        finally:
            conn.close()
    
    def list_remotes(self) -> List[Tuple]:
        """List all remotes"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, name, comment FROM Remote ORDER BY name")
        remotes = cursor.fetchall()
        conn.close()
        
        return remotes
    
    def get_remote(self, remote_id: int) -> Optional[Tuple]:
        """Get remote by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, name, comment FROM Remote WHERE id = ?", (remote_id,))
        remote = cursor.fetchone()
        conn.close()
        
        return remote
    
    def add_key(self, remote_id: int, protocol: str, address: str, command: str, 
                key_name: str, comment: str = None):
        """Add a new key to a remote"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO Key (remote_id, protocol, address, command, key_name, comment)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (remote_id, protocol, address, command, key_name, comment))
            conn.commit()
        finally:
            conn.close()


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
        print("\nWhat would you like to do?")
        print("1 - Create a new remote")
        print("2 - List remotes")
        print("3 - Register new keys")
        print("q - Quit")
        print()
    
    def create_new_remote(self):
        """Handle creating a new remote"""
        print("\n--- Create New Remote ---")
        
        name = input("Enter remote name: ").strip()
        if not name:
            print("Error: Remote name cannot be empty")
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
        while True:
            print("Waiting for IR codes... (Press ESC to exit)")

            # Check for ESC key
            if InputHandler.check_escape():
                print("\nExiting key registration mode")
                break
            
            # Check for serial data
            line = None
            if self.serial_handler.is_connected():
                line = self.serial_handler.read_line()
            
            if line:
                # Parse the received data
                try:
                    parts = line.split(';')
                    if len(parts) <= 3:
                        print(f"Invalid data format: {line} need at least 3 parts separated by ';'")
                        continue
                    
                    protocol, addr, command = parts[0:3]
                    print(f"Received: Protocol={protocol}, Address={addr}, Command={command}")
                    
                    # Get key name
                    key_name = None
                    while not key_name:
                        key_name = input("Enter key name: ").strip()
                        if not key_name:
                            print("You must input a key name or press " " (SPACE) to cancel.")
                    
                    if key_name == ' ':
                        print("Key registration cancelled for this code.")
                        continue
                    
                    # Get optional comment
                    comment = input("Enter comment (optional): ").strip()
                    comment = comment if comment else None
                    
                    # Save to database
                    self.db.add_key(remote_id, protocol, addr, command, key_name, comment)
                    print(f"Key '{key_name}' saved successfully")
                    
                except Exception as e:
                    print(f"Error saving key: {e}")
        
        # Cleanup
        self.serial_handler.disconnect()
    
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


def main():
    """Entry point"""
    parser = argparse.ArgumentParser(description='IR Remote Cloner - Capture and store IR remote codes')
    parser.add_argument('--port', '-p', 
                       default='/dev/ttyUSB0',
                       help='Serial port to connect to (default: /dev/ttyUSB0)')
    parser.add_argument('--baudrate', '-b', 
                       default='9600',
                       help='Baud rate for serial communication (default: 9600)')    
    
    args = parser.parse_args()
    
    app = IRRemoteCloner(serial_port=args.port, baudrate=args.baudrate)
    app.run()


if __name__ == "__main__":
    main()
