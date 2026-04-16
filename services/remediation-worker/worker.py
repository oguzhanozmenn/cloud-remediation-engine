import boto3
import os
import time
import json
from botocore.exceptions import EndpointConnectionError

# 1. Ortam Değişkenlerini Yapılandır (K8s veya Docker'dan gelir)
ENDPOINT_URL = os.getenv("AWS_ENDPOINT_URL", "http://host.docker.internal:4566")
AWS_REGION = os.getenv("AWS_REGION", "eu-central-1")
QUEUE_NAME = "security-alerts-queue"


def fix_s3_bucket(bucket_name):
    """Kovanın Public Access ayarlarını kapatan fonksiyon"""
    try:
        s3 = boto3.client('s3', endpoint_url=ENDPOINT_URL, region_name=AWS_REGION)
        print(f"🛠️ Müdahale Başladı: {bucket_name} kovası güvenli hale getiriliyor...")

        s3.put_public_access_block(
            Bucket=bucket_name,
            PublicAccessBlockConfiguration={
                'BlockPublicAcls': True,
                'IgnorePublicAcls': True,
                'BlockPublicPolicy': True,
                'RestrictPublicBuckets': True
            }
        )
        print(f"✅ Başarılı: {bucket_name} artık dış dünyaya kapalı!")
    except Exception as e:
        print(f"❌ S3 düzeltme hatası: {e}")


def start_worker():
    print(f"🤖 Worker başlatıldı... Hedef Endpoint: {ENDPOINT_URL}")

    while True:
        try:
            # SQS Bağlantısını kur
            sqs = boto3.client('sqs', endpoint_url=ENDPOINT_URL, region_name=AWS_REGION)

            # Kuyruk URL'sini al
            queue_url = sqs.get_queue_url(QueueName=QUEUE_NAME)['QueueUrl']

            # Mesaj bekle (Long Polling)
            response = sqs.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=5
            )

            if 'Messages' in response:
                for message in response['Messages']:
                    # HATA BURADAYDI: message['MessageBody'] değil, message['Body'] olmalı
                    body = json.loads(message['Body'])
                    bucket_name = body.get('bucket_name')

                    if bucket_name:
                        fix_s3_bucket(bucket_name)

                    # İşlem bitince mesajı kuyruktan sil
                    sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=message['ReceiptHandle'])

            else:
                print("☁️ Kuyruk boş, dinlemeye devam ediyorum...")

        except EndpointConnectionError:
            print(f"⚠️ LocalStack'e ulaşılamıyor ({ENDPOINT_URL}). 5 saniye sonra tekrar denenecek...")
            time.sleep(5)
        except Exception as e:
            if "QueueDoesNotExist" in str(e):
                print(f"⚠️ Kuyruk ({QUEUE_NAME}) henüz oluşturulmamış. Bekleniyor...")
            else:
                print(f"🔥 Beklenmedik hata: {e}")
            time.sleep(5)


if __name__ == "__main__":
    start_worker()