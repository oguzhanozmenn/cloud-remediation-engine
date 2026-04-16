import boto3
import json

# 1. LocalStack Bağlantı Ayarları
# Trigger sadece kuyruğa mesaj atacağı için SQS client'ı yeterli.
sqs = boto3.client(
    'sqs',
    region_name="eu-central-1",
    endpoint_url="http://localhost:4566", # LocalStack adresi
    aws_access_key_id="test",
    aws_secret_access_key="test"
)

# 2. Kuyruğun Adresini (URL) Alalım
# Terraform ile oluşturduğumuz kuyruğun adını yazıyoruz.
QUEUE_NAME = "security-alerts-queue"

try:
    queue_url = sqs.get_queue_url(QueueName=QUEUE_NAME)['QueueUrl']

    # 3. İhbar Mesajını Hazırlayalım
    # Worker bu JSON'u okuyup hangi kovayı (bucket) düzelteceğini anlayacak.
    event_payload = {
        "bucket_name": "sirket-ozel-veriler"
    }

    # 4. Mesajı Kuyruğa Gönderelim
    sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps(event_payload)
    )

    print(f"🚨 [SİMÜLASYON] 'sirket-ozel-veriler' kovası için zafiyet alarmı fırlatıldı!")
    print(f"📩 Mesaj SQS kuyruğuna ({QUEUE_NAME}) başarıyla iletildi.")

except Exception as e:
    print(f"❌ Hata oluştu: {e}")