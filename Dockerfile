FROM python:3.11-slim

# Create a non-root user
RUN useradd -m vaultuser

WORKDIR /home/vaultuser/app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV FLASK_ENV production

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Ensure upload directory exists and has correct permissions
RUN mkdir -p uploads && chown -R vaultuser:vaultuser /home/vaultuser/app

USER vaultuser

EXPOSE 8000

# Start Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "wsgi:app"]
