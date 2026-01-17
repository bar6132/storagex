import redis
import os
from datetime import timedelta

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

try:
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    r.ping()
    print("✅ Redis Connected Successfully")
except Exception as e:
    print(f"⚠️ Redis connection failed: {e}")
    r = None

def get_cached_summary(video_id: str):
    """Retrieve summary from RAM (Fast)"""
    if not r: return None
    return r.get(f"summary:{video_id}")

def set_cached_summary(video_id: str, summary: str, expire_hours=24):
    """Save summary to RAM for 24 hours"""
    if not r: return
    r.setex(f"summary:{video_id}", timedelta(hours=expire_hours), summary)

# --- RATE LIMIT ---
def check_rate_limit(user_ip: str, limit=5, window_seconds=60):
    if not r: return True
    key = f"rate_limit:{user_ip}"
    current = r.incr(key)
    if current == 1: r.expire(key, window_seconds)
    return current <= limit