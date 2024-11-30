import os
from flask import Flask, request, jsonify
import mysql.connector
from mysql.connector import Error
import base64
from io import BytesIO
from PIL import Image
import ddddocr
from datetime import datetime

app = Flask(__name__)

# Database configuration from environment variables
db_config = {
    'host': os.getenv('DB_HOST'),
    'port': int(os.getenv('DB_PORT', 1337)), 
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME')
}

ocr = ddddocr.DdddOcr()

# Function to validate user
def is_user_valid(device_id, session_id):
    if session_id == '0':
        return False

    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        query = """
            SELECT 1
            FROM user_sessions
            WHERE device_id = %s
              AND session_id = %s
              AND subscription_date >= %s
            LIMIT 1
        """
        current_date = datetime.now().strftime('%Y-%m-%d')
        cursor.execute(query, (device_id, session_id, current_date))
        result = cursor.fetchone()
        return result is not None  # 若存在匹配行，返回 True
    except Error:
        return False
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'connection' in locals() and connection:
            connection.close()


# Function to process image and perform OCR
def process_image_and_recognize(image_data):
    try:
        image_bytes = base64.b64decode(image_data)
        image = Image.open(BytesIO(image_bytes)).convert('RGB')
        image_bytes = BytesIO()
        image.save(image_bytes, format="PNG")
        result = ocr.classification(image_bytes.getvalue())
        return result
    except Exception:
        return None

# Route to handle OCR request
@app.route('/ocr/b64', methods=['POST'])
def ocr_service():
    try:
        request_data = request.get_json()

        if not request_data or 'device_id' not in request_data or 'session_id' not in request_data:
            return jsonify({"error": "Missing device_id or session_id in request body"}), 400

        device_id = request_data['device_id']
        session_id = request_data['session_id']

        if not is_user_valid(device_id, session_id):
            return jsonify({"error": "Invalid user"}), 403

        if 'image' not in request_data:
            return jsonify({"error": "Missing 'image' key in request body"}), 402

        image_data = request_data['image']
        result = process_image_and_recognize(image_data)

        if result:
            return jsonify({"ocr_result": result}), 200
        else:
            return jsonify({"error": "Failed to process image"}), 501

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv('PORT', 1337)), debug=True)
