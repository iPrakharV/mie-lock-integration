import sys
import time
from pn532 import *

# Create an instance of the PN532 class.
pn532 = PN532_I2C(debug=False, reset=20, req=16)

# Setup NFC
try:
    pn532.SAM_configuration()
except Exception as e:
    print(f"Unable to set up NFC reader, check the connection. Error: {e}")
    sys.exit()

print("NFC Reader setup complete!")

# Variables to store card data
last_type = 'NONE'
PAN_and_ExpDate = ''
UID_and_Secret = ''
sent_message = False

def read_emv():
    # Selecting MasterCard AID
    apdu_select_aid = [
        0x00, 0xA4, 0x04, 0x00, 0x07, 0xA0, 0x00, 0x00, 0x00, 0x04, 0x10, 0x10, 0x00
    ]
    response = pn532.call_function(apdu_select_aid)
    if response:
        # Process the response data, extract PAN, Expiry, etc.
        print("Received AID response:", response)
        return response
    return None

def read_iso14443a():
    uid = pn532.read_passive_target(timeout=0.5)
    if uid:
        print("Found an ISO14443A card with UID:", [hex(i) for i in uid])
        return uid
    return None

def main():
    global last_type, PAN_and_ExpDate, UID_and_Secret, sent_message

    while True:
        # Reset card state if removed
        if last_type != 'NONE' and not pn532.read_passive_target(timeout=0.1):
            print(f"{last_type} card removed")
            last_type = 'NONE'
            sent_message = False
            PAN_and_ExpDate = ''
            UID_and_Secret = ''

        if last_type == 'NONE':
            emv_response = read_emv()
            if emv_response:
                last_type = 'EMV'
                # Additional processing to extract PAN and Expiry
                continue

            iso_response = read_iso14443a()
            if iso_response:
                last_type = 'ISO14443A'
                # Additional processing to extract UID and other data
                continue

        # Additional handling for sending messages or performing other actions
        # This is where you could add MQTT publishing or other logic

        time.sleep(1)

if __name__ == "__main__":
    main()