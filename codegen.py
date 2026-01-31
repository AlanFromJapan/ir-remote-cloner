
#from IRProtocol.h
from enum import Enum
from db import Database
from terminal_colors import terminal_colors


class Protocol(Enum):
    UNKNOWN = 0
    PULSE_WIDTH = 1
    PULSE_DISTANCE = 2
    APPLE = 3
    DENON = 4
    JVC = 5
    LG = 6
    LG2 = 7
    NEC = 8
    NEC2 = 9
    ONKYO = 10
    PANASONIC = 11
    KASEIKYO = 12
    KASEIKYO_DENON = 13
    KASEIKYO_SHARP = 14
    KASEIKYO_JVC = 15
    KASEIKYO_MITSUBISHI = 16
    RC5 = 17
    RC6 = 18
    RC6A = 19
    SAMSUNG = 20
    SAMSUNGLG = 21
    SAMSUNG48 = 22
    SHARP = 23
    SONY = 24


def protocol_to_string(protocol_id: int) -> str:
    try:
        protocol = Protocol(protocol_id)
    except ValueError:
        return "UNKNOWN"
    return protocol.name


def protocol_to_arduino_signature(protocol_id: int) -> str:
    try:
        protocol = Protocol(protocol_id)
    except ValueError:
        return "Unknown"
    
    if protocol == Protocol.PULSE_WIDTH:
        return "PulseWidth"
    elif protocol == Protocol.PULSE_DISTANCE:
        return "PulseDistance"
    elif protocol == Protocol.APPLE:
        return "Apple"
    elif protocol == Protocol.DENON:
        return "Denon"
    elif protocol == Protocol.JVC:
        return "JVC"
    elif protocol == Protocol.LG:
        return "LG"
    elif protocol == Protocol.LG2:
        return "LG2"
    elif protocol == Protocol.NEC:
        return "NEC"
    elif protocol == Protocol.NEC2:
        return "NEC2"
    elif protocol == Protocol.ONKYO:
        return "Onkyo"
    elif protocol == Protocol.PANASONIC:
        return "Panasonic"
    elif protocol == Protocol.KASEIKYO:
        return "Kaseikyo"
    elif protocol == Protocol.KASEIKYO_DENON:
        return "Kaseikyo_Denon"
    elif protocol == Protocol.KASEIKYO_SHARP:
        return "Kaseikyo_Sharp"
    elif protocol == Protocol.KASEIKYO_JVC:
        return "Kaseikyo_JVC"
    elif protocol == Protocol.KASEIKYO_MITSUBISHI:
        return "Kaseikyo_Mitsubishi"
    elif protocol == Protocol.RC5:
        return "RC5"
    elif protocol == Protocol.RC6:
        return "RC6"
    elif protocol == Protocol.RC6A:
        return "RC6A"
    elif protocol == Protocol.SAMSUNG:
        return "Samsung"
    elif protocol == Protocol.SAMSUNGLG:
        return "SamsungLG"
    elif protocol == Protocol.SAMSUNG48:
        return "Samsung48"
    elif protocol == Protocol.SHARP:
        return "Sharp"
    elif protocol == Protocol.SONY:
        return "Sony"
    else:
        return "Unknown"
    

def generate_arduino_code(remote_id: int):
    # Generate Arduino code for the given remote ID on the standard output
    db = Database()
    remote = db.get_remote(remote_id)
    if not remote:
        print(f"Remote with ID {remote_id} not found.")
        return
    remote_name = remote[1]

    keys = db.get_keys_for_remote(remote_id)
    if not keys:
        print(f"No keys found for remote '{remote_name}'.")
        return  
    
    print(f"{terminal_colors.OKGREEN}// Arduino code for remote: {remote_name}")
    print("// Start from the code of IRremote library sample 'SimpleSender' and overwrite the whole code with below.\n")

    print("#include <Arduino.h>")
    print("#include \"PinDefinitionsAndMore.h\"")
    print("#include <IRremote.hpp>\n")
    print("IRsend irsend;\n")
    print("void setup() {")
    print("\t// Nothing to setup")
    print("}\n")
    
    print("void loop() {")
    print("\tuint8_t sRepeats = 0;  // Adjust repeat count as needed\n")

    for key in keys:
        key_name, protocol_id, address, command, _ = key
        protocol_sign = protocol_to_arduino_signature(int(protocol_id))
        protocol_name = protocol_to_string(int(protocol_id))
        print(f"\t// Sending key: {key_name} = CMD {command} ({hex(int(command))}) at ADDR {address} ({hex(int(address))}) using protocol: [{protocol_id}] {protocol_name}")
        print(f"\tirsend.send{protocol_sign}({address}, {command}, sRepeats);")
        print("\tdelay(2000);  // Wait 2 seconds between commands")
        print("")

    print(f"}}{terminal_colors.ENDC}")
