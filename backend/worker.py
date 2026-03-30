import pika
import json
import os
import subprocess
import requests
from database import SessionLocal
from models import VideoJob
from tasks import S3_CLIENT
import datetime
import time

API_URL = os.getenv("INTERNAL_API_URL", "http://api:8002/internal/notify")
INTERNAL_NOTIFY_SECRET = os.getenv("INTERNAL_NOTIFY_SECRET", "")

def send_notification(user_id, video_id, status, message):
    try:
        headers = {}
        if INTERNAL_NOTIFY_SECRET:
            headers["X-Internal-Token"] = INTERNAL_NOTIFY_SECRET
        payload = {
            "user_id": user_id,
            "video_id": video_id,
            "status": status,
            "message": message
        }
        requests.post(API_URL, json=payload, headers=headers, timeout=5)
    except Exception as e:
        print(f"[!] Notification failed: {e}")

def process_video(job_id, input_filename, resolution="720p"):
    db = SessionLocal()
    job = db.query(VideoJob).filter(VideoJob.id == job_id).first()

    if not job:
        print(f"Job {job_id} not found.")
        return

    local_input = f"/tmp/{input_filename.split('/')[-1]}"
    local_output = f"/tmp/processed_{job_id}.mp4"

    try:
        send_notification(job.owner_id, job_id, "processing", "Processing started...")

        job.status = "processing"
        db.commit()
        print(f"[*] Processing job {job_id} ({resolution})...")

        s3_output_key = f"processed/user_{job.owner_id}/{job_id}.mp4"

        S3_CLIENT.download_file("raw-videos", input_filename, local_input)

        res_map = {"1080p": 1080, "720p": 720, "480p": 480}
        target_h = res_map.get(resolution, 720)

        ffmpeg_cmd = [
            "ffmpeg", "-y", "-i", local_input,
            "-vf", f"scale=-2:{target_h}",
            "-c:v", "libx264", "-crf", "23", "-preset", "veryfast",
            "-c:a", "aac", "-b:a", "128k",
            local_output
        ]

        subprocess.run(ffmpeg_cmd, check=True)

        S3_CLIENT.upload_file(local_output, "processed-videos", s3_output_key)

        job.status = "completed"
        job.s3_key = s3_output_key
        job.processed_at = datetime.datetime.utcnow()
        db.commit()

        send_notification(job.owner_id, job_id, "completed", "Video is ready!")

        try:
            S3_CLIENT.delete_object(Bucket="raw-videos", Key=input_filename)
        except Exception:
            pass

        print(f"[#] Job {job_id} completed.")

    except Exception as e:
        print(f"[!] Error: {e}")
        job.status = "failed"
        db.commit()
        send_notification(job.owner_id, job_id, "failed", "Processing failed")
    finally:
        if os.path.exists(local_input): os.remove(local_input)
        if os.path.exists(local_output): os.remove(local_output)
        db.close()

def callback(ch, method, properties, body):
    data = json.loads(body)
    res = data.get('resolution', '720p')
    process_video(data['job_id'], data['filename'], res)
    ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    rabbitmq_host = os.getenv("RABBITMQ_HOST", "rabbitmq")
    rabbitmq_user = os.getenv("RABBITMQ_USER", "guest")
    rabbitmq_pass = os.getenv("RABBITMQ_PASS", "guest")
    credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_pass)

    connection = None
    while not connection:
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=rabbitmq_host, credentials=credentials, heartbeat=600)
            )
        except Exception:
            print("Retrying RabbitMQ...")
            time.sleep(5)

    channel = connection.channel()
    QUEUE_NAME = 'video_tasks'
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)

    print(' [*] Worker Ready')
    channel.start_consuming()

if __name__ == "__main__":
    main()
