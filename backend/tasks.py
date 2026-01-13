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

def notify_worker(job_id, filename, resolution="720p"):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
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
    """Generate a presigned URL to share an S3 object"""
    try:
        response = S3_CLIENT.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': bucket,
                'Key': object_name
            },
            ExpiresIn=expiration
        )
        return response.replace("minio:9000", "localhost:9000")
    except Exception as e:
        print(f"Error generating URL: {e}")
        return None