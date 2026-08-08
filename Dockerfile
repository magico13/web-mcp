# Use Python 3.13 slim image as base
FROM python:3.14-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py .
COPY duckduckgo_search.py .
COPY goggles.py .
COPY web_wrapper.py .
COPY nws_forecast.py .

# Expose port 8000
EXPOSE 8000

# Run the application
CMD ["python", "app.py"]
