import requests
import json
import os
import cv2
import base64
import time
from minio import Minio
from sqlalchemy.orm import Session
from cache import get_cached_summary, set_cached_summary
import models

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434/api/generate")
VISION_MODEL = "moondream"   # The Eyes
TEXT_MODEL = "llama3.2:1b"   # The Brain

MINIO_CLIENT = Minio(
    "minio:9000",
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False
)

def get_frame_at_percentage(video_path, percentage):
    """Extracts a single frame at a specific percentage (0.2, 0.5, 0.8)"""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened(): return None
    
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(total_frames * percentage))
    
    ret, frame = cap.read()
    cap.release()
    
    if not ret: return None
    _, buffer = cv2.imencode('.jpg', frame)
    return base64.b64encode(buffer).decode('utf-8')

def analyze_image_with_moondream(image_b64):
    """Asks Moondream to describe technical details in the image"""
    prompt = "Describe the software interface in this image. List any visible buttons, text inputs, headers, or specific words like 'Chat', 'Model', 'AI', or code."
    
    try:
        response = requests.post(OLLAMA_URL, json={
            "model": VISION_MODEL,
            "prompt": prompt,
            "images": [image_b64],
            "stream": False
        }, timeout=30)
        return response.json().get("response", "")
    except:
        return ""

def synthesize_final_summary(descriptions):
    """Asks Llama 3.2 to combine descriptions into a factual summary"""
    combined_text = "\n".join([f"- Frame {i+1}: {desc}" for i, desc in enumerate(descriptions)])
    prompt = (
        f"You are a visual analysis AI. Here are descriptions of three frames from a video:\n\n"
        f"{combined_text}\n\n"
        f"Task: Identify the subject matter and write a 3-sentence summary.\n"
        f"1. Analyze the visual cues. Are they organic (nature, people) or digital (screens, games)?\n"
        f"2. If the descriptions mention 'flowers', 'sun', or 'nature', describe it as a vlog or nature clip.\n"
        f"3. If the descriptions mention 'code', 'text', or 'interface', describe it as a technical video.\n"
        f"4. DO NOT hallucinate details not present in the descriptions.\n\n"
        f"Final Summary:"
    )

    try:
        response = requests.post(OLLAMA_URL, json={
            "model": TEXT_MODEL,
            "prompt": prompt,
            "stream": False
        }, timeout=30)
        return response.json().get("response", "Analysis failed.")
    except:
        return "Could not synthesize summary."

def generate_summary_stream(video_id: str, video_title: str, db: Session, ignore_cache: bool = False):
    if not ignore_cache:
        cached = get_cached_summary(video_id)
        if cached: return cached
        
        db_summary = db.query(models.VideoSummary).filter(models.VideoSummary.video_id == video_id).first()
        if db_summary:
            set_cached_summary(video_id, db_summary.summary_text)
            return db_summary.summary_text

    if ignore_cache:
        print(f"♻️ Force regenerating for {video_id}...")
        db.query(models.VideoSummary).filter(models.VideoSummary.video_id == video_id).delete()
        db.commit()

    print(f"👁️ Analyzing video story for: {video_id}")
    video = db.query(models.VideoJob).filter(models.VideoJob.id == video_id).first()
    if not video or not video.s3_key: return "Video not ready."

    temp_filename = f"/tmp/{video_id}.mp4"
    try:
        MINIO_CLIENT.fget_object("processed-videos", video.s3_key, temp_filename)

        timestamps = [0.2, 0.5, 0.8]
        descriptions = []
        
        for t in timestamps:
            img = get_frame_at_percentage(temp_filename, t)
            if img:
                desc = analyze_image_with_moondream(img)
                descriptions.append(desc)
                print(f"   --> Frame at {int(t*100)}%: {desc[:50]}...")

        if not descriptions:
            final_summary = "Could not analyze video visual content."
        else:
            final_summary = synthesize_final_summary(descriptions)

        os.remove(temp_filename)
        
        new_summary = models.VideoSummary(video_id=video_id, summary_text=final_summary)
        db.add(new_summary)
        db.commit()
        set_cached_summary(video_id, final_summary)
        
        return final_summary

    except Exception as e:
        print(f"Error: {e}")
        return "Analysis failed."