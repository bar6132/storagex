import pika
import json
import os
import subprocess
from database import SessionLocal
from models import VideoJob 
from tasks import S3_CLIENT
import datetime
import time

def process_video(job_id, input_filename):
    db = SessionLocal()
    job = db.query(VideoJob).filter(VideoJob.id == job_id).first()
    
    if not job:
        print(f"Job {job_id} not found.")
        return

    try:
        job.status = "processing"
        db.commit()
        print(f"[*] Processing job {job_id} for User {job.owner_id}...")

        local_input = f"/tmp/{input_filename.split('/')[-1]}"
        local_output = f"/tmp/processed_{job_id}.mp4"
        
        s3_output_key = f"processed/user_{job.owner_id}/{job_id}.mp4"

        S3_CLIENT.download_file("raw-videos", input_filename, local_input)

        ffmpeg_cmd = [
            "ffmpeg", "-y", "-i", local_input,
            "-vf", "scale=-1:720",
            "-c:v", "libx264", "-crf", "23", "-preset", "veryfast",
            local_output
        ]
        subprocess.run(ffmpeg_cmd, check=True)

        S3_CLIENT.upload_file(local_output, "processed-videos", s3_output_key)

        job.status = "completed"
        job.s3_key = s3_output_key
        job.processed_at = datetime.datetime.utcnow()
        db.commit()
        print(f"[#] Job {job_id} completed successfully.")

    except Exception as e:
        print(f"[!] Error processing job {job_id}: {e}")
        job.status = "failed"
        db.commit()
    finally:
        if os.path.exists(local_input): os.remove(local_input)
        if os.path.exists(local_output): os.remove(local_output)
        db.close()

def callback(ch, method, properties, body):
    data = json.loads(body)
    process_video(data['job_id'], data['filename'])
    ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    connection = None
    while not connection:
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host='rabbitmq', heartbeat=600)
            )
        except pika.exceptions.AMQPConnectionError:
            print("[!] RabbitMQ not ready, retrying in 5 seconds...")
            time.sleep(5)

    channel = connection.channel()
    channel.queue_declare(queue='video_tasks', durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='video_tasks', on_message_callback=callback)

    print(' [*] Worker waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

if __name__ == "__main__":
    main()