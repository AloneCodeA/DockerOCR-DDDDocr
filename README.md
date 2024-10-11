# DockerOCR-DDDDocr
DockerOCR is a lightweight Flask application that processes base64-encoded images, applies image thresholding, and uses OCR (Optical Character Recognition) to extract text. The app includes retry logic with adjustable image processing parameters to improve recognition accuracy, making it ideal for handling noisy or distorted images.
Here’s a `README.md` file for your project based on the Dockerfile and your Flask OCR service setup:

---
FlaskOCRService is a lightweight application that processes base64-encoded images, applies image thresholding, and uses OCR (Optical Character Recognition) to extract text. The service runs on a Flask web server and is containerized using Docker for easy deployment.

## Features
- Processes images via POST requests with base64-encoded data.
- Performs OCR on images using `ddddocr`.
- Retries image processing with adjustable thresholds for better recognition accuracy.
- Easily deployable as a Docker container.

## Requirements
- Python 3.9
- Flask
- ddddocr
- NumPy
- OpenCV (for image processing)
- PIL (Pillow)

## Installation

### 1. Clone the repository:
```bash
cd FlaskOCRService
```

### 2. Install dependencies:
```bash
pip install -r requirements.txt
```

### 3. Run the Flask application:
```bash
python NewOcr.py
```

The Flask application will be running at `http://localhost:3049`.

## Using Docker

You can also build and run the project using Docker.

### 1. Build the Docker image:
```bash
docker build -t flask-ocr-service .
```

### 2. Run the Docker container:
```bash
docker run -p 3049:3049 flask-ocr-service
```

### Dockerfile

This project uses the following `Dockerfile` to containerize the application:

```dockerfile
# Use an official Python runtime as a parent image
FROM python:3.9-slim-buster

# Set the working directory in the container
WORKDIR /usr/src/app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system level dependencies for OpenCV
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
 && rm -rf /var/lib/apt/lists/*

# Install any needed packages specified in requirements.txt
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Make port 3049 available to the world outside this container
EXPOSE 3049

# Run your application when the container launches
CMD ["python", "./NewOcr.py"]
```

## API Endpoints

### 1. `GET /`
**Description:** A simple health check endpoint.

### 2. `POST /ocr/b64`
**Description:** Processes the provided base64-encoded image and returns the OCR result.

**Request Example:**
```json
{
    "image_data": "base64_encoded_image_here"
}
```

**Response Example:**
- 200 OK: Returns the recognized text from the image.
- 400 Bad Request: If no image data is provided.
- 500 Internal Server Error: If an error occurs during processing.

## License
This project is licensed under the MIT License.

---

This `README.md` includes sections for setup, Docker instructions, API usage, and a description of your project. Let me know if you'd like any changes!
