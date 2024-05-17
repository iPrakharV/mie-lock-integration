import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522

rfid = SimpleMFRC522()

counter = 0

while True:
        
        if counter % 1000 == 0:
            print("Reading RFID...")

        id, text = rfid.read()
        print(f"ID: {id}\nText: {text}")
