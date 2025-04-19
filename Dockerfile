FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download NLTK data
RUN python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet')"

# Copy the rest of the application
COPY . .

# Create upload directory
RUN mkdir -p uploads

# Expose the port
EXPOSE 8080

# Command to run the application with Gunicorn
CMD gunicorn --bind 0.0.0.0:$PORT app:app