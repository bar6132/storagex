import boto3
import pika
import os
import json

S3_CLIENT = boto3.client(
    's3',
    endpoint_url=os.getenv("S3_ENDPOINT", "http://minio:9000"),
    aws_access_key_id="minioadmin",
    aws_secret_access_key="minioadmin"
)

def upload_to_s3(file_obj, bucket, object_name):
    S3_CLIENT.upload_fileobj(file_obj, bucket, object_name)
    return object_name

def notify_worker(job_id, filename):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()
    channel.queue_declare(queue='video_tasks', durable=True)
    
    message = json.dumps({"job_id": job_id, "filename": filename})
    
    channel.basic_publish(
        exchange='',
        routing_key='video_tasks',
        body=message,
        properties=pika.BasicProperties(delivery_mode=2) 
    )
    connection.close()