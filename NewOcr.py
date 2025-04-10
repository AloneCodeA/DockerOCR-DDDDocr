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

# 初始化 OCR 模型
ocr_cn = ddddocr.DdddOcr()
ocr_eng = ddddocr.DdddOcr(show_ad=False, ocr=True)


# 驗證用戶是否有效
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
        return cursor.fetchone() is not None
    except Error:
        return False
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'connection' in locals(): connection.close()


# 解碼 base64 並轉換為圖片 bytes
def extract_image_bytes(image_b64):
    try:
        image_bytes = base64.b64decode(image_b64)
        image = Image.open(BytesIO(image_bytes)).convert('RGB')
        output = BytesIO()
        image.save(output, format="PNG")
        return output.getvalue()
    except Exception:
        return None


# 通用 OCR 路由處理函式
def handle_ocr_request(request_data, ocr_engine):
    if not request_data:
        return jsonify({"error": "Missing JSON body"}), 400

    device_id = request_data.get('device_id')
    session_id = request_data.get('session_id')
    image_data = request_data.get('image')

    if not device_id or not session_id:
        return jsonify({"error": "Missing device_id or session_id"}), 400

    if not is_user_valid(device_id, session_id):
        return jsonify({"error": "Invalid user"}), 403

    if not image_data:
        return jsonify({"error": "Missing 'image' key in request body"}), 402

    image_bytes = extract_image_bytes(image_data)
    if image_bytes is None:
        return jsonify({"error": "Invalid or corrupt image data"}), 400

    result = ocr_engine.classification(image_bytes)
    if result:
        return jsonify({"ocr_result": result}), 200
    else:
        return jsonify({"error": "Failed to process image"}), 501


# 中文驗證碼 OCR
@app.route('/ocr/b64', methods=['POST'])
def ocr_service():
    try:
        request_data = request.get_json()
        return handle_ocr_request(request_data, ocr_cn)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 英文 OCR
@app.route('/ocr/b64/eng', methods=['POST'])
def ocr_service_eng():
    try:
        request_data = request.get_json()
        return handle_ocr_request(request_data, ocr_eng)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv('PORT', 1337)), debug=True)
