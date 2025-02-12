from flask import Flask, request, jsonify
from cryptography.fernet import Fernet
import base64

app = Flask(__name__)

# Encryption key and cipher suite
KEY = None
cipher_suite = None

def decrypt_data(encrypted_text):  # Decrypting the data using Fernet
    if cipher_suite is None:
        return "Error: Encryption key not set."

    return cipher_suite.decrypt(base64.b64decode(encrypted_text)).decode()


@app.route("/set_key", methods=["POST"])
def set_key():
    global KEY, cipher_suite
    data = request.json

    if "key" not in data:
        return jsonify({"status": "error", "message": "Key not provided"}), 400

    KEY = base64.b64decode(data["key"])  # Decode the base64 key
    cipher_suite = Fernet(KEY)  # Initialize the cipher suite

    return jsonify({"status": "success", "message": "Key received"})


@app.route("/upload", methods=["POST"])
def upload():

    global img_counter

    if cipher_suite is None:
        return jsonify({"status": "error", "message": "Encryption key not set"}), 400

    data = request.json
    try:
        license_plate = decrypt_data(data["license_plate"])
        timestamp = decrypt_data(data["timestamp"])
        image_base64 = decrypt_data(data["image"])

        image_path = f"captured_images/{license_plate}_{timestamp}.jpg"

        with open(image_path, "wb") as img_file:
            img_file.write(base64.b64decode(image_base64))

        print(f"Received: Plate={license_plate}, Timestamp={timestamp}")

        return jsonify({"status": "success", "message": "Data received"})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
