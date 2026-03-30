"""
Queue-depth auto-scaler for StorageX workers.

Polls RabbitMQ every SCALER_INTERVAL seconds and scales the
'worker' service containers up or down based on pending jobs.

Scale table (JOBS_PER_WORKER = 2):
  0 jobs  → 1 worker  (minimum)
  2 jobs  → 2 workers
  4 jobs  → 3 workers
  6 jobs  → 4 workers
  8+ jobs → 5 workers (maximum)

Scale-down has a 2-cycle cooldown (~30 s) to prevent flapping.
"""

import os
import time
import requests
import docker

# ── Config ──────────────────────────────────────────────────────────────────
RABBITMQ_API   = os.getenv("RABBITMQ_API",   "http://rabbitmq:15672/api/queues/%2F/video_tasks")
RABBITMQ_USER  = os.getenv("RABBITMQ_USER",  "guest")
RABBITMQ_PASS  = os.getenv("RABBITMQ_PASS",  "guest")

CHECK_INTERVAL  = int(os.getenv("SCALER_INTERVAL",   "15"))   # seconds between checks
MIN_WORKERS     = int(os.getenv("MIN_WORKERS",        "1"))
MAX_WORKERS     = int(os.getenv("MAX_WORKERS",        "5"))
JOBS_PER_WORKER = int(os.getenv("JOBS_PER_WORKER",   "2"))    # jobs that trigger +1 worker

# ── Docker client ────────────────────────────────────────────────────────────
client = docker.from_env()


def get_queue_depth() -> int | None:
    """Returns the number of messages waiting in the video_tasks queue."""
    try:
        r = requests.get(
            RABBITMQ_API,
            auth=(RABBITMQ_USER, RABBITMQ_PASS),
            timeout=5
        )
        r.raise_for_status()
        return r.json().get("messages", 0)
    except Exception as e:
        print(f"[!] Queue check failed: {e}")
        return None


def get_running_workers():
    """Returns a list of running worker containers (identified by compose label)."""
    return client.containers.list(
        filters={
            "label": "com.docker.compose.service=worker",
            "status": "running"
        }
    )


def desired_worker_count(queue_depth: int) -> int:
    count = MIN_WORKERS + (queue_depth // JOBS_PER_WORKER)
    return max(MIN_WORKERS, min(MAX_WORKERS, count))


def scale_up(n: int, reference):
    """Start n new worker containers cloned from a reference container."""
    attrs   = reference.attrs
    image   = attrs["Config"]["Image"]
    cmd     = attrs["Config"]["Cmd"]
    env     = attrs["Config"]["Env"]
    labels  = dict(attrs["Config"]["Labels"])

    # Pick the first attached network
    networks = list(attrs["NetworkSettings"]["Networks"].keys())
    network  = networks[0] if networks else None

    for _ in range(n):
        try:
            c = client.containers.run(
                image=image,
                command=cmd,
                environment=env,
                network=network,
                labels=labels,
                detach=True,
            )
            print(f"[+] Worker started: {c.short_id}")
        except Exception as e:
            print(f"[!] Failed to start worker: {e}")


def scale_down(workers, target: int):
    """Gracefully stop excess worker containers (newest first)."""
    extras = workers[target:]
    for c in extras:
        print(f"[-] Stopping worker {c.short_id} ...")
        try:
            c.stop(timeout=30)
            c.remove()
        except Exception as e:
            print(f"[!] Failed to stop {c.short_id}: {e}")


def main():
    print("[*] Auto-scaler started")
    scale_down_ticks = 0   # cooldown counter

    while True:
        depth = get_queue_depth()

        if depth is None:
            time.sleep(CHECK_INTERVAL)
            continue

        workers = get_running_workers()
        current = len(workers)
        desired = desired_worker_count(depth)

        if desired > current:
            scale_down_ticks = 0   # reset cooldown
            print(f"[~] Queue={depth}  workers {current} → {desired}  (scale UP)")
            if workers:
                scale_up(desired - current, workers[0])
            else:
                print("[!] No reference worker container found — cannot scale up")

        elif desired < current:
            scale_down_ticks += 1
            if scale_down_ticks >= 2:   # ~30 s of low load before shrinking
                print(f"[~] Queue={depth}  workers {current} → {desired}  (scale DOWN)")
                scale_down(workers, desired)
                scale_down_ticks = 0
            else:
                print(f"[~] Queue={depth}  workers {current}  (cooldown {scale_down_ticks}/2 before scale-down)")

        else:
            scale_down_ticks = 0
            print(f"[=] Queue={depth}  workers={current}  OK")

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
