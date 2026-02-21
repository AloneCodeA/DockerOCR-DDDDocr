import os
import base64
from io import BytesIO
from datetime import datetime
from flask import Flask, request, jsonify
from PIL import Image
import mysql.connector
from mysql.connector import Error
import ddddocr

app = Flask(__name__)

# 資料庫設定
db_config = {
    'host': os.getenv('DB_HOST'),
    'port': int(os.getenv('DB_PORT', 1337)), 
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME')
}

ocr = ddddocr.DdddOcr()

# ✅ 抽出共用請求解析邏輯
def extract_request_fields(data):
    missing = []
    device_id = data.get('device_id')
    session_id = data.get('session_id')
    image_data = data.get('image')

    if not device_id:
        missing.append("device_id")
    if not session_id:
        missing.append("session_id")
    if not image_data:
        missing.append("image")

    if missing:
        return None, None, None, jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    return device_id, session_id, image_data, None, None

# ✅ 驗證使用者是否合法
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
        cursor.execute(query, (device_id, session_id, datetime.now().strftime('%Y-%m-%d')))
        return cursor.fetchone() is not None
    except Error:
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()

# ✅ 處理圖片並執行 OCR，支援自訂範圍與機率模式
def create_ocr_result(image_data, charset_range=None):
    try:
        image_bytes = base64.b64decode(image_data)
        image = Image.open(BytesIO(image_bytes)).convert('RGB')
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        img_data = buffer.getvalue()

        if charset_range is not None:
            ocr.set_ranges(charset_range)
            result = ocr.classification(img_data, probability=True)
            return ''.join(result['charsets'][i.index(max(i))] for i in result['probability'])
        else:
            return ocr.classification(img_data)

    except Exception:
        return None

# ✅ 通用處理函數
def handle_ocr_request(charset_range=None):
    try:
        request_data = request.get_json()
        device_id, session_id, image_data, error_response, status = extract_request_fields(request_data)
        if error_response:
            return error_response, status

        if not is_user_valid(device_id, session_id):
            return jsonify({"error": "Invalid user"}), 403

        result = create_ocr_result(image_data, charset_range)
        if result:
            return jsonify({"ocr_result": result}), 200
        else:
            return jsonify({"error": "Failed to process image"}), 501

    except Exception as e:
        return jsonify({"error": f"Internal error: {str(e)}"}), 500

# 路由：純數字
@app.route('/ocr/b64', methods=['POST'])
def ocr_digits():
    return handle_ocr_request(charset_range=0)

# 路由：小寫英文 + 空格
@app.route('/ocr/b64/eng', methods=['POST'])
def ocr_lowercase_with_space():
    return handle_ocr_request(charset_range="abcdefghijklmnopqrstuvwxyz ")

# 啟動 Flask
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv('PORT', 1337)), debug=True)
