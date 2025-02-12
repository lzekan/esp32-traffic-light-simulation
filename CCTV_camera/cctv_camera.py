import cv2
import easyocr
import numpy as np
import paho.mqtt.client as mqtt
import requests
import base64
from cryptography.fernet import Fernet
import datetime
import os

# Generating an encryption key
KEY = Fernet.generate_key()
cipher_suite = Fernet(KEY)

# MQTT and server configuration
MQTT_BROKER = "192.168.39.139"
MQTT_TOPIC = "motion/detected"
SERVER_URL = "http://192.168.39.139:5000/upload"
SERVER_URL_KEY = "http://192.168.39.139:5000/set_key"

# EasyOCR Reader
reader = easyocr.Reader(['en'])

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()


def send_key():
    # Sends the encryption key to the server
    response = requests.post(SERVER_URL_KEY, json={"key": base64.b64encode(KEY).decode()})

    if response.status_code == 200:
        print("Key successfully sent to the server.")
    else:
        print(f"Error sending key: {response.text}")


def encrypt_data(data):
    # Fernet encryption
    return base64.b64encode(cipher_suite.encrypt(data.encode())).decode()


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT broker.")
        client.subscribe(MQTT_TOPIC)
    else:
        print(f"Failed to connect, return code {rc}")


def on_message(client, userdata, msg):
    print("Motion detected! Capturing image...")

    ret, frame = cap.read()
    if not ret:
        print("Failed to capture image.")
        return

    timestamp = datetime.datetime.now().strftime("%Y-%d-%m %H-%M-%S")  # Moment of capturing the image

    # OCR Processing
    license_plate = "UNKNOWN"
    results = reader.readtext(frame)

    for (bbox, text, prob) in results:
        print(f"License plate detected: {text} (Confidence: {prob:.2f})")
        if prob > 0.5:  # Only write out the licenses he is over 50% sure of
            license_plate = text

            pts = np.array([(int(pt[0]), int(pt[1])) for pt in bbox], dtype=np.int32)
            cv2.polylines(frame, [pts], isClosed=True, color=(0, 255, 0), thickness=2)  # Drawing the bounding box

    image_path = "captured_image.jpg"  # Saving the captured image
    cv2.imwrite(image_path, frame)

    with open(image_path, "rb") as img_file:
        img_base64 = base64.b64encode(img_file.read()).decode()  # Encode image as base64

    encrypted_data = {
        "license_plate": encrypt_data(license_plate),
        "timestamp": encrypt_data(timestamp),
        "image": encrypt_data(img_base64),
    }

    os.remove("captured_image.jpg")

    try:
        response = requests.post(SERVER_URL, json=encrypted_data)
        if response.status_code == 200:
            print("Data successfully sent to the server.")
        else:
            print(f"Server error: {response.status_code}, {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")


# Send encryption key to the server
send_key()

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

try:
    client.connect(MQTT_BROKER, 1883, 60)
    client.loop_forever()
except Exception as e:
    print(f"MQTT connection error: {e}")
