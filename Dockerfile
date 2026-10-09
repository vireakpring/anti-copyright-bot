FROM python:3.10-slim

# ដំឡើង FFmpeg និង System Dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy និង ដំឡើង Python Libraries
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy កូដទាំងអស់ចូល
COPY . .

# បើក Port សម្រាប់ Streamlit
EXPOSE 8501

# Command សម្រាប់ Run App
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
