# Dockerfile
FROM python:3.9-slim

# Set work directory
WORKDIR /app

# Copy code
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Make upload dir
RUN mkdir -p static/uploads

# Expose port
EXPOSE 5000

# Run the app
CMD ["python", "app.py"]

