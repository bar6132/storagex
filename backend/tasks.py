import boto3
import pika
import os
import json

S3_CLIENT = boto3.client(
    's3',
    endpoint_url=os.getenv("S3_ENDPOINT", "http://minio:9000"),
    aws_access_key_id=os.getenv("S3_ACCESS_KEY", "minioadmin"),
    aws_secret_access_key=os.getenv("S3_SECRET_KEY", "minioadmin")
)

def upload_to_s3(file_obj, bucket, object_name):
    S3_CLIENT.upload_fileobj(file_obj, bucket, object_name)
    return object_name

def notify_worker(job_id, filename, resolution="720p"):
    rabbitmq_host = os.getenv("RABBITMQ_HOST", "rabbitmq")
    rabbitmq_user = os.getenv("RABBITMQ_USER", "guest")
    rabbitmq_pass = os.getenv("RABBITMQ_PASS", "guest")
    credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_pass)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=rabbitmq_host, credentials=credentials)
    )
    channel = connection.channel()

    QUEUE_NAME = 'video_tasks'
    channel.queue_declare(queue=QUEUE_NAME, durable=True)

    message = json.dumps({
        "job_id": job_id,
        "filename": filename,
        "resolution": resolution
    })

    channel.basic_publish(
        exchange='',
        routing_key=QUEUE_NAME,
        body=message,
        properties=pika.BasicProperties(delivery_mode=2)
    )
    connection.close()

def get_presigned_url(object_name, bucket="processed-videos", expiration=3600):
    """Generate a presigned URL for an S3 object — valid for 1 hour by default."""
    try:
        response = S3_CLIENT.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket, 'Key': object_name},
            ExpiresIn=expiration
        )
        # Rewrite internal Docker hostname to the externally accessible address
        s3_internal = os.getenv("S3_ENDPOINT", "http://minio:9000").replace("http://", "").replace("https://", "")
        s3_public = os.getenv("S3_PUBLIC_URL", "http://localhost:9000").replace("http://", "").replace("https://", "")
        return response.replace(s3_internal, s3_public)
    except Exception as e:
        print(f"Error generating presigned URL: {e}")
        return None
