from flask import Flask, request
import numpy as np
import cv2 as cv
import base64
from PIL import Image
import ddddocr
import random
import io
from io import BytesIO

app = Flask(__name__)

# Initialize the OCR model
ocr = ddddocr.DdddOcr()

def process_image_and_recognize(image_data, bin_threshold=58, bin_increment=2, retry_attempts=5):
    """
    Processes the base64-encoded image, applies thresholding, and performs OCR.
    
    Args:
    - image_data (str): Base64-encoded image string.
    - bin_threshold (int): The initial threshold value for blue channel comparison.
    - bin_increment (int): Increment applied to the threshold in each retry.
    - retry_attempts (int): Number of times to retry OCR with increased threshold.
    
    Returns:
    - str: Recognized result or a random 2-digit number if OCR fails.
    """
    image_bytes = base64.b64decode(image_data)
    image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    results = []

    for _ in range(retry_attempts):
        img_array = np.array(image)
        
        # Apply binary threshold based on blue channel intensity
        for i in range(img_array.shape[1]):
            for j in range(img_array.shape[0]):
                (red, green, blue) = img_array[j, i]
                if (blue - red > bin_threshold) or (blue - green > bin_threshold):
                    img_array[j, i] = [255, 255, 255]  # Set to white
                else:
                    img_array[j, i] = [0, 0, 0]  # Set to black

        processed_image = Image.fromarray(img_array)

        # Convert processed image to bytes
        with BytesIO() as output:
            processed_image.save(output, format="PNG")
            image_bytes = output.getvalue()

        # Perform OCR
        ocr_result = ocr.classification(image_bytes)

        # Correct commonly confused characters
        corrected_result = (
            ocr_result.replace('o', '0').replace('O', '0')
            .replace('i', '1').replace('I', '1')
            .replace('l', '1').replace('s', '5')
            .replace('S', '5').replace('z', '2')
            .replace('Z', '2').replace('b', '6')
        )

        # Check if the result is a valid 2-digit number
        if len(corrected_result) == 2 and corrected_result.isdigit():
            results.append(corrected_result)

        # Increase threshold for the next retry
        bin_threshold += bin_increment

    # Return the most common result or a random 2-digit number if none found
    if results:
        return max(set(results), key=results.count)
    else:
        return "{:02d}".format(random.randint(1, 99))


@app.route('/', methods=['GET'])
def ping():
    """
    Basic route to check if the server is running.
    """
    return "Working"

@app.route('/ocr/b64', methods=['POST'])
def ocr_service():
    """
    OCR service that accepts base64-encoded image data in POST request.
    """
    try:
        request_data = request.get_data().decode('utf-8')
        if request_data:
            result = process_image_and_recognize(request_data)
            return result, 200
        else:
            return "No image data provided", 400
    except Exception as e:
        return str(e), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3049, debug=True)
