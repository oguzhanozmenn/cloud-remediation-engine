# Hafif bir Python imajı seçiyoruz
FROM python:3.11-slim

# Çalışma dizinini belirliyoruz
WORKDIR /app

# Bağımlılıkları kopyalayıp yüklüyoruz
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Worker kodunu içeriye aktarıyoruz
COPY worker.py .

# Uygulamayı başlatıyoruz
CMD ["python", "worker.py"]
# Dockerfile içine ekle
ENV PYTHONUNBUFFERED=1