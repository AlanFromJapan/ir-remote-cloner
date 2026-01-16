#!/usr/bin/env python3
"""
Test script for IR Remote Cloner database functionality
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import Database

def test_database():
    """Test database operations"""
    # Use a test database
    db = Database("test_ir_remotes.db")
    
    print("Testing database functionality...")
    
    # Test creating remotes
    try:
        remote1_id = db.create_remote("Samsung TV", "Living room TV")
        print(f"✓ Created remote 'Samsung TV' with ID: {remote1_id}")
        
        remote2_id = db.create_remote("Sony Receiver")
        print(f"✓ Created remote 'Sony Receiver' with ID: {remote2_id}")
    except Exception as e:
        print(f"✗ Error creating remotes: {e}")
        return False
    
    # Test listing remotes
    try:
        remotes = db.list_remotes()
        print(f"✓ Retrieved {len(remotes)} remotes")
        for remote_id, name, comment in remotes:
            print(f"  - ID: {remote_id}, Name: {name}, Comment: {comment}")
    except Exception as e:
        print(f"✗ Error listing remotes: {e}")
        return False
    
    # Test adding keys
    try:
        db.add_key(remote1_id, "NEC", "0xFF629D", "0x0", "Power", "Power on/off")
        print("✓ Added power key to Samsung TV")
        
        db.add_key(remote1_id, "NEC", "0xFF906F", "0x0", "Volume Up", "Increase volume")
        print("✓ Added volume up key to Samsung TV")
        
        db.add_key(remote2_id, "RC5", "0x1234", "0x5678", "Input", "Switch input")
        print("✓ Added input key to Sony Receiver")
    except Exception as e:
        print(f"✗ Error adding keys: {e}")
        return False
    
    # Test getting specific remote
    try:
        remote = db.get_remote(remote1_id)
        if remote:
            print(f"✓ Retrieved remote by ID: {remote[1]}")
        else:
            print("✗ Could not retrieve remote by ID")
            return False
    except Exception as e:
        print(f"✗ Error getting remote: {e}")
        return False
    
    print("\n✓ All database tests passed!")
    
    # Cleanup
    os.remove("test_ir_remotes.db")
    print("✓ Test database cleaned up")
    
    return True

if __name__ == "__main__":
    success = test_database()
    sys.exit(0 if success else 1)