FROM python:3.11-slim

# Prevent Python from writing .pyc files and bufferless logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install Python dependencies first to improve build caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

EXPOSE 8050

# Run the Dash app with Gunicorn
CMD ["gunicorn", "app:server", "--bind", "0.0.0.0:8050"]