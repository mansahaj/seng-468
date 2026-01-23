FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ /app/
COPY scripts/ /app/scripts/

# Expose port
EXPOSE 5000

# Run application
CMD ["python", "app.py"]
