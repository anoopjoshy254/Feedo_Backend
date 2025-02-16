import serial
import time

# Open serial connection (Replace 'COM10' with your actual port)
ser = serial.Serial('COM11', 9600, timeout=1)  
time.sleep(2)  # Wait for the connection to establish

# Send "START" as a string
command = "STOP\n"  # Include newline for easier parsing
ser.write(command.encode())  # Convert string to bytes and send

print(f"Command SENT: {command}")

ser.close()  # Close the connection
