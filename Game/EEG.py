import serial
import time
import threading
from collections import deque
from constants import SF, BUFFER_SEC  # Sampling Frequency & Buffer Duration

class EEGDevice:
    """
    EEGDevice handles communication with a ThinkGear-like EEG device.
    Runs in a separate thread for real-time signal processing.
    """
    def __init__(self, port, baudrate=57600):
        try:
            self.ser = serial.Serial(port, baudrate, timeout=0.1)  # Faster response
        except serial.SerialException as e:
            print(f"ERROR: Cannot open serial port {port}: {e}")
            exit(1)

        self.eeg_buffer = deque(maxlen=SF * BUFFER_SEC)  
        self.attention_value = 50
        self.meditation_value = 50
        self.quality = 0
        self.blink = 0
        self.data = {}

        self.running = True
        self.thread = threading.Thread(target=self.fetch_data_loop, daemon=True)
        self.thread.start()  # Start real-time data fetching in the background

        print(f"EEG Device Initialized on {port} at {baudrate} baud.")

    def fetch_data_loop(self):
        """
        Runs in a background thread to fetch EEG data in real-time.
        """
        while self.running:
            self.fetch_data()
            self.print_values()  # Print real-time Attention & Meditation
            time.sleep(0.005)  # Prevent CPU overuse (adjust if needed)

    def fetch_data(self):
        """
        Reads one data packet from the EEG device, verifies the checksum,
        and updates the EEG buffer.
        """
        try:
            if self.ser.in_waiting < 2:
                return  # Skip if not enough data

            # Read until sync bytes (0xAA 0xAA)
            sync = self.ser.read_until(b'\xaa\xaa')
            if len(sync) < 2:
                return  

            # Read packet length
            packet_length = self.ser.read(1)
            if not packet_length:
                return  
            packet_length = packet_length[0]

            # Read payload
            payload = self.ser.read(packet_length)
            if len(payload) != packet_length:
                return  

            # Verify checksum
            checksum = sum(payload) & 0xFF
            checksum = (~checksum) & 0xFF
            received_checksum = self.ser.read(1)
            if not received_checksum or received_checksum[0] != checksum:
                return  # Skip invalid packets

            # Reset data for this packet
            self.data = {}

            # Parse payload
            i = 0
            while i < len(payload):
                code = payload[i]
                i += 1

                if code >= 0x80:  # Extended code
                    if i >= len(payload):
                        return  
                    length = payload[i]
                    i += 1
                    if code == 0x80 and length == 2:  # EEG raw data
                        if i + 1 >= len(payload):
                            return  
                        val0, val1 = payload[i], payload[i + 1]
                        raw_value = (val0 << 8) | val1
                        if raw_value > 32768:
                            raw_value -= 65536
                        self.eeg_buffer.append(raw_value)
                        self.data['eeg_raw'] = raw_value
                        i += 2
                    else:
                        i += length
                else:  # Simple code
                    if i >= len(payload):
                        return  
                    value = payload[i]
                    i += 1

                    if code == 0x02:  # Signal quality
                        self.quality = value
                    elif code == 0x04:  # Attention
                        self.attention_value = value
                    elif code == 0x05:  # Meditation
                        self.meditation_value = value

        except Exception as e:
            print(f"Error in fetch_data: {e}")

    def print_values(self):
        """Prints Attention & Meditation values in real-time."""
        print(f"🧠 Attention: {self.attention_value} | 🧘 Meditation: {self.meditation_value}")

    def close(self):
        self.running = False
        self.thread.join()
        if self.ser.is_open:
            self.ser.close()
        print("EEG serial connection closed.")

