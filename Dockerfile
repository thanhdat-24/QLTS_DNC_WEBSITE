# Sử dụng Python base image
FROM python:3.9-slim

# Cài đặt thư viện cần thiết
RUN apt-get update && apt-get install -y gcc

# Tạo thư mục trong container
WORKDIR /app

# Copy các file cần thiết
COPY . /app

# Cài đặt các thư viện từ requirements
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Khai báo biến môi trường nếu cần
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Chạy app bằng Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:create_app()"]
