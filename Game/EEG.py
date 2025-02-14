import serial
import time
from collections import deque
from constants import SF, BUFFER_SEC

class EEGDevice:
    """
    EEGDevice handles communication with a ThinkGear-like EEG device.
    It reads packets from the serial port, verifies the checksum,
    and updates the raw EEG buffer along with attention and meditation levels.
    """
    def __init__(self, port, baudrate=57600):
        try:
            # Open the serial port with a timeout to avoid hanging
            self.ser = serial.Serial(port, baudrate, timeout=2)
        except serial.SerialException as e:
            print(f"ERROR: Unable to open serial port {port}: {e}")
            exit(1)

        # Circular buffer to store raw EEG data
        self.eeg_buffer = deque(maxlen=SF * BUFFER_SEC)
        # Set default values to neutral (50) so the EEG-controlled ball stays still
        self.attention_value = 50
        self.meditation_value = 50

        # Other EEG metrics
        self.quality = 0
        self.blink = 0
        # A dictionary to hold the latest data packet values
        self.data = {}

        print(f"EEG Device Initialized on {port} at {baudrate} baud.")

    def fetch_data(self):
        """
        Reads one data packet from the EEG device, verifies the checksum,
        and updates the raw EEG buffer along with attention and meditation levels.
        """
        try:
            # Wait for sync bytes (0xAA 0xAA)
            sync = self.ser.read_until(b'\xaa\xaa')
            if not sync.endswith(b'\xaa\xaa'):
                raise ValueError("Sync bytes not received properly.")

            # Read packet length
            packet_length_byte = self.ser.read(1)
            if not packet_length_byte:
                raise ValueError("No packet length byte received.")
            packet_length = packet_length_byte[0]

            # Read payload and calculate checksum
            payload = []
            checksum_calc = 0
            for _ in range(packet_length):
                byte = self.ser.read(1)
                if not byte:
                    raise ValueError("Incomplete payload received.")
                payload.append(byte)
                checksum_calc += byte[0]
            checksum_calc = (~checksum_calc) & 0xff

            # Read transmitted checksum
            checksum_byte = self.ser.read(1)
            if not checksum_byte:
                raise ValueError("No checksum byte received.")
            if checksum_byte[0] != checksum_calc:
                raise ValueError("Checksum mismatch.")

            # Reset the data dictionary for this packet
            self.data = {}

            # Parse the payload
            i = 0
            while i < len(payload):
                code = payload[i][0]
                i += 1

                if code >= 0x80:
                    # Extended code: the next byte is the length of the data
                    if i >= len(payload):
                        raise ValueError("Payload truncated after code.")
                    length = payload[i][0]
                    i += 1

                    # Handle raw EEG data (code 0x80 with 2 data bytes)
                    if code == 0x80 and length == 2:
                        if i + 1 >= len(payload):
                            raise ValueError("Incomplete raw EEG data.")
                        val0 = payload[i][0]
                        val1 = payload[i + 1][0]
                        raw_value = val0 * 256 + val1
                        if raw_value > 32768:
                            raw_value -= 65536
                        self.eeg_buffer.append(raw_value)
                        self.data['eeg_raw'] = raw_value
                        i += 2
                    else:
                        # Skip or handle other extended codes if needed
                        i += length
                else:
                    # Simple code: the next byte is the value
                    if i >= len(payload):
                        raise ValueError("Missing value for code.")
                    value = payload[i][0]
                    i += 1

                    if code == 0x02:         # Signal quality
                        self.quality = value
                        self.data['quality'] = value
                    elif code == 0x04:       # Attention level
                        self.attention_value = value
                        self.data['attention'] = value
                    elif code == 0x05:       # Meditation level
                        self.meditation_value = value
                        self.data['meditation'] = value
                    else:
                        # For any unhandled codes, store them in the data dictionary
                        self.data[f'code_{code:02x}'] = value

        except Exception as e:
            print(f"Error in fetch_data: {e}")

    def close(self):
        if self.ser.is_open:
            self.ser.close()
            print("EEG serial connection closed.")
