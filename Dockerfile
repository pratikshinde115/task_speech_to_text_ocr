# Use an official Python image as the base
FROM python:3.9

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Tesseract OCR (for OCR functionality)
RUN apt-get update && apt-get install -y tesseract-ocr && rm -rf /var/lib/apt/lists/*

# Copy the rest of the application code
COPY . .

# Expose any necessary ports (if applicable)
EXPOSE 5000  # Adjust if needed

# Command to run the application
CMD ["python", "app.py"]
