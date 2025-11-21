# Arduino LED Matrix Controller

A Python-based control interface for MAX7219 8×8 LED matrix modules using Streamlit and Arduino.

## Overview

This project provides a web-based interface for controlling a MAX7219 LED matrix connected to an Arduino Uno. The application supports scrolling text, grid-based pattern design, and freehand drawing with automatic downsampling to 8×8 resolution.

## Features

- **Text Scrolling**: Display scrolling text messages with adjustable speed
- **Grid Editor**: Design patterns using an interactive 8×8 checkbox grid
- **Drawing Canvas**: Create freehand drawings that are automatically converted to 8×8 patterns
- **Serial Communication**: Real-time control over USB serial connection

## Hardware Requirements

### Components

- Arduino Uno R3
- MAX7219 8×8 LED matrix module
- USB cable (Type A to Type B)
- Jumper wires or breadboard

### Wiring Configuration

| MAX7219 Pin | Arduino Pin | Function |
|-------------|-------------|----------|
| VCC | 5V | Power supply |
| GND | GND | Ground |
| DIN | D12 | Data input |
| CLK | D11 | Clock signal |
| CS/LOAD | D10 | Chip select |

**Note**: Ensure common ground between Arduino and LED matrix module.

## Software Requirements

- Python 3.9 or higher
- Arduino IDE
- pip package manager

## Installation

### 1. Clone Repository

```bash
git clone <repository-url>
cd <project-directory>
```

### 2. Set Up Python Environment

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Upload Arduino Firmware

1. Open `firmware.ino` in Arduino IDE
2. Select **Tools** > **Board** > **Arduino Uno**
3. Select **Tools** > **Port** > [Your Arduino Port]
4. Click **Upload**

## Usage

### Starting the Application

```bash
streamlit run app.py
```

The application will open in your default browser at `http://localhost:8501`.

### Configuration

**Sidebar Settings:**

1. **Serial Port**: Select the appropriate port
   - Windows: `COM3`, `COM4`, etc.
   - macOS/Linux: `/dev/ttyACM0`, `/dev/ttyUSB0`, etc.
2. **Baud Rate**: Set to `115200` (must match firmware)
3. Click **Connect/Reconnect** to establish connection

### Operating Modes

#### Text Mode

- Enter ASCII text in the input field
- Adjust scroll speed using the slider (milliseconds per frame)
- Text is rendered and scrolled across the display automatically

#### Click Grid

- Toggle individual LEDs using the 8×8 checkbox grid
- Click **Update Matrix** to send the pattern to hardware
- Useful for designing static icons and testing LED orientation

#### Draw Mode

- Draw freehand on the 256×256 pixel canvas
- Drawing is automatically downsampled to 8×8 resolution
- Click **Send Drawing** to display the pattern on the matrix
- Ideal for quick prototyping of shapes and symbols

## Serial Protocol

### Communication Parameters

- **Baud Rate**: 115200
- **Data Bits**: 8
- **Stop Bits**: 1
- **Parity**: None

### Frame Format

Each frame consists of 9 bytes:

- Byte 0: Header (`0xAA`)
- Bytes 1-8: Row data (one byte per row)

**Row Encoding:**
- Each byte represents one row (top to bottom)
- Each bit represents one column (bit 7 = leftmost, bit 0 = rightmost)
- Bit value: `1` = LED on, `0` = LED off

## Project Structure

```
.
├── app.py                 # Streamlit application
├── firmware.ino           # Arduino firmware
├── requirements.txt       # Python dependencies
└── README.md             # Documentation
```

## Dependencies

```text
streamlit>=1.38
pyserial>=3.5
Pillow>=10.0
numpy>=1.24
streamlit-drawable-canvas>=0.9.3
```

## Troubleshooting

### Display Issues

**No output on matrix:**
- Verify all wiring connections
- Confirm Arduino firmware is uploaded
- Check that correct serial port is selected
- Ensure matrix is not in shutdown mode

**Mirrored or rotated display:**
- Horizontal mirroring is corrected in software
- For 90° or 180° rotation, modify the transformation logic in `app.py`

### Connection Issues

**Serial connection fails:**
- Ensure no other application is using the serial port
- Close Arduino IDE Serial Monitor if open
- Verify correct port and baud rate selection

**Connection lost after browser refresh:**
- Click **Connect/Reconnect** in sidebar
- Serial connection is not persistent across page reloads

## Future Development

- Support for cascaded MAX7219 modules (extended displays)
- Animation presets and sequences
- Pattern save/load functionality
- Brightness control interface
- REST API for external integration

## License

This project is provided as-is for educational and hobbyist purposes.