import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522

rfid = SimpleMFRC522()

while True:
        id, text = rfid.read()
        print(f"ID: {id}\nText: {text}")
