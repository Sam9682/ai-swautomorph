FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    sqlite3 \
    curl \
    git \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directory for database
RUN mkdir -p /app/data

# Expose port
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV SECRET_KEY=change-this-in-production

# Create SSH setup script
RUN echo '#!/bin/bash\n\
eval "$(ssh-agent -s)"\n\
for key in /root/.ssh/OVH_SW_AUTOMORPH*; do\n\
  if [ -f "$key" ] && [[ "$key" != *.pub ]]; then\n\
    ssh-add "$key" 2>/dev/null || true\n\
  fi\n\
done\n\
exec "$@"' > /app/start.sh && chmod +x /app/start.sh

# Initialize database and start application
CMD ["/app/start.sh", "python3", "app.py"]