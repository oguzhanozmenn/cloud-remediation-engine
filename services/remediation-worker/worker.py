import boto3
import os
import time
import json
from botocore.exceptions import EndpointConnectionError
from prometheus_client import start_http_server, Counter, Summary

# --- PROMETHEUS METRİKLERİ ---
# Başarılı onarımları sayacak metrik
REMEDIATIONS_TOTAL = Counter('cloud_remediation_total', 'Toplam düzeltilen güvenlik ihlali sayısı')
# İşlem süresini ölçecek metrik
PROCESS_TIME = Summary('remediation_processing_seconds', 'Düzeltme işleminin saniye cinsinden süresi')

# 1. Ortam Değişkenlerini Yapılandır
ENDPOINT_URL = os.getenv("AWS_ENDPOINT_URL", "http://host.docker.internal:4566")
AWS_REGION = os.getenv("AWS_REGION", "eu-central-1")
QUEUE_NAME = "security-alerts-queue"
METRICS_PORT = 8000  # Prometheus'un veriyi çekeceği port


@PROCESS_TIME.time()  # Fonksiyonun ne kadar sürdüğünü otomatik ölçer
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
        REMEDIATIONS_TOTAL.inc()  # Başarılı işlem sonrası sayacı 1 artır

    except Exception as e:
        print(f"❌ S3 düzeltme hatası: {e}")


def start_worker():
    # Metrik sunucusunu ayrı bir thread gibi arka planda başlatır
    print(f"📊 Metrik sunucusu port {METRICS_PORT} üzerinde başlatıldı...")
    start_http_server(METRICS_PORT)

    print(f"🤖 Worker başlatıldı... Hedef Endpoint: {ENDPOINT_URL}")

    while True:
        try:
            sqs = boto3.client('sqs', endpoint_url=ENDPOINT_URL, region_name=AWS_REGION)
            queue_url = sqs.get_queue_url(QueueName=QUEUE_NAME)['QueueUrl']

            response = sqs.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=5
            )

            if 'Messages' in response:
                for message in response['Messages']:
                    body = json.loads(message['Body'])
                    bucket_name = body.get('bucket_name')

                    if bucket_name:
                        fix_s3_bucket(bucket_name)

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