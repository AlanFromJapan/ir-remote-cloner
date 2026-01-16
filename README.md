# IR Remote Cloner

A command line application to capture, store, and manage IR remote control codes using a serial-connected device (like an Arduino with IR receiver).

## Features

- **SQLite Database Storage**: Stores remotes and their key codes in a local SQLite database
- **Serial Communication**: Connects to devices via serial port to receive IR codes
- **Remote Management**: Create and list IR remotes with descriptions
- **Key Registration**: Capture IR codes and associate them with labeled keys
- **Minimal Dependencies**: Uses standard Python libraries where possible

## Installation

1. Clone this repository
2. Install the required dependency:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the application:
```bash
python app.py
```

### Menu Options

1. **Create a New Remote**: Register a new remote control device with name and optional comment
2. **List Remotes**: Display all registered remotes in a table format
3. **Register New Keys**: Capture IR codes for a specific remote

### Serial Device Format

The application expects serial data in the format:
```
protocol;code1;code2
```

For example:
```
NEC;0xFF629D;0x0
RC5;0x1234;0x5678
```

### Database Schema

The application creates two tables:

- **Remote**: Stores remote information (id, name, comment)
- **Key**: Stores individual key codes (id, remote_id, protocol, code1, code2, key_name, comment)

## Hardware Requirements

- Serial device (e.g., Arduino with IR receiver) that sends IR codes in the expected format
- Default serial port: `/dev/ttyUSB0` (configurable during key registration)
- Default baud rate: 9600

## Controls

- During key registration, press **ESC** to exit the registration loop
- Use **Ctrl+C** to quit the application at any time

## Error Handling

- The application gracefully handles missing pyserial installation
- Invalid serial ports are handled with warnings
- Database integrity is maintained with unique constraints
- Input validation prevents empty or invalid entries
