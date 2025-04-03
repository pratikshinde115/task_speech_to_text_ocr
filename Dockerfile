# Use an official Python image as the base
FROM python:3.9

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    libasound2-dev \
    libjack-dev \
    tesseract-ocr \
    poppler-utils  # <-- Install Poppler for pdf2image support

# Copy the requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose any necessary ports (if applicable)
EXPOSE 5000  

# Command to run the application
CMD ["python", "app.py"]
