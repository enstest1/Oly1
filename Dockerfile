# Use slim Python 3.11 as base
FROM python:3.11-slim

# Install basic OS packages
RUN apt-get update && \
    apt-get install -y curl unzip && \
    rm -rf /var/lib/apt/lists/*

# Download and install oyl CLI (update this URL if needed)
RUN curl -Lo /usr/local/bin/oyl https://github.com/oylxyz/cli/releases/latest/download/oyl-linux && \
    chmod +x /usr/local/bin/oyl

# Set working directory
WORKDIR /app

# Copy dependency file first (for layer caching)
COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy rest of your app code
COPY . .

# Run the clock-in bot
CMD ["python", "auto_clockin.py"]
