from fastapi import APIRouter, BackgroundTasks, Depends, UploadFile, File, HTTPException, status, Form
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
import os
import models, schemas, database, tasks, main_utils
import search
import cache
from sqlalchemy.orm import joinedload
import ai_utils

router = APIRouter(prefix="/videos", tags=["Videos"])

ALLOWED_CONTENT_TYPES = {
    "video/mp4", "video/mpeg", "video/quicktime", "video/x-msvideo",
    "video/x-matroska", "video/webm", "video/x-flv", "video/3gpp",
    "video/x-ms-wmv", "video/ogg",
}
ALLOWED_EXTENSIONS = {".mp4", ".mpeg", ".mov", ".avi", ".mkv", ".webm", ".flv", ".3gp", ".wmv", ".ogv"}
MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2 GB

@router.get("/feed", response_model=List[schemas.VideoOut])
def get_video_feed(
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(database.get_db)
):
    limit = min(limit, 100)
    query = db.query(models.VideoJob).filter(
        models.VideoJob.is_shared == True,
        models.VideoJob.is_deleted == False
    )
    if category and category != "All":
        query = query.filter(models.VideoJob.category == category)
    return query.order_by(desc(models.VideoJob.created_at)).offset(skip).limit(limit).all()

@router.post("/upload", response_model=schemas.VideoOut)
async def create_upload_job(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: str = Form(None),
    category: str = Form("Other"),
    is_shared: bool = Form(False),
    resolution: str = Form("720p"),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(main_utils.get_current_user)
):
    # Validate file type (both extension and content-type header)
    file_ext = os.path.splitext(file.filename or "")[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS or file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only video files are accepted (mp4, mov, avi, mkv, webm, etc.)"
        )

    # Validate file size
    file_size = file.size
    if file_size is None:
        # Read a chunk to get size if Content-Length not provided
        content = await file.read()
        file_size = len(content)
        await file.seek(0)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Maximum allowed size is 2 GB.")

    if not current_user.is_admin:
        current_usage = db.query(func.sum(models.VideoJob.file_size)).filter(
            models.VideoJob.owner_id == current_user.id,
            models.VideoJob.is_deleted == False
        ).scalar() or 0
        if current_usage + file_size > current_user.storage_limit:
            raise HTTPException(status_code=400, detail="Storage quota exceeded!")

    new_job = models.VideoJob(
        filename=file.filename,
        title=title,
        description=description,
        category=category,
        is_shared=is_shared,
        owner_id=current_user.id,
        status="pending",
        file_size=file_size
    )
    db.add(new_job)
    db.commit()

    if is_shared:
        search.index_video(new_job.id, new_job.title, description, category)

    db.refresh(new_job)

    s3_filename = f"raw/user_{current_user.id}/{new_job.id}-{file.filename}"
    await file.seek(0)
    tasks.upload_to_s3(file.file, "raw-videos", s3_filename)
    tasks.notify_worker(new_job.id, s3_filename, resolution)

    return new_job

@router.get("/my-videos", response_model=List[schemas.VideoOut])
async def list_videos(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(main_utils.get_current_user)
):
    return db.query(models.VideoJob).filter(
        models.VideoJob.owner_id == current_user.id,
        models.VideoJob.is_deleted == False
    ).all()

@router.get("/status/{job_id}", response_model=schemas.VideoOut)
async def get_job_status(job_id: str, db: Session = Depends(database.get_db)):
    job = db.query(models.VideoJob).filter(models.VideoJob.id == job_id).first()
    if not job: raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.delete("/{video_id}")
async def delete_video(
    video_id: str,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(main_utils.get_current_user)
):
    video = db.query(models.VideoJob).filter(models.VideoJob.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    if not current_user.is_admin and video.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    if current_user.is_admin:
        try:
            from tasks import S3_CLIENT
            raw_path = f"raw/user_{video.owner_id}/{video.id}-{video.filename}"
            S3_CLIENT.delete_object(Bucket="raw-videos", Key=raw_path)
            if video.s3_key:
                S3_CLIENT.delete_object(Bucket="processed-videos", Key=video.s3_key)
        except Exception as e:
            print(f"S3 Purge failed: {e}")

        db.delete(video)
        db.commit()
        return {"message": "Admin: Video purged permanently"}
    else:
        video.is_deleted = True
        db.commit()
        return {"message": "Video moved to trash"}

@router.get("/search", response_model=List[schemas.VideoOut])
def search_public_videos(
    q: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(database.get_db)
):
    query = db.query(models.VideoJob).options(
        joinedload(models.VideoJob.summary_data)
    ).filter(
        models.VideoJob.is_shared == True,
        models.VideoJob.is_deleted == False
    )

    if category and category != "All":
        query = query.filter(models.VideoJob.category == category)

    if q:
        # Limit search query length to prevent abuse
        q = q[:200]
        try:
            video_ids = search.search_videos(q, None)
        except Exception as e:
            print(f"Search failed: {e}")
            video_ids = []

        if not video_ids:
            return []

        query = query.filter(models.VideoJob.id.in_(video_ids))

    return query.order_by(models.VideoJob.created_at.desc()).all()

@router.get("/play/{video_id}")
async def get_video_url(
    video_id: str,
    db: Session = Depends(database.get_db),
    current_user: Optional[models.User] = Depends(main_utils.get_current_user_optional)
):
    video = db.query(models.VideoJob).filter(models.VideoJob.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    is_owner = current_user and (video.owner_id == current_user.id or current_user.is_admin)
    is_public = getattr(video, "is_shared", False)
    if not is_public and not is_owner:
        raise HTTPException(status_code=403, detail="Not authorized to view this private video")

    if not video.s3_key:
        raise HTTPException(status_code=400, detail="Video is not ready yet")

    url = tasks.get_presigned_url(video.s3_key, "processed-videos")
    if not url:
        raise HTTPException(status_code=500, detail="Could not generate playback link")

    return {"url": url}

@router.get("/admin/all", response_model=List[schemas.VideoOut])
async def get_all_videos_admin(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(main_utils.get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    limit = min(limit, 200)
    videos = db.query(models.VideoJob).options(
        joinedload(models.VideoJob.owner)
    ).offset(skip).limit(limit).all()

    results = []
    for video in videos:
        results.append({
            "id": video.id,
            "filename": video.filename,
            "title": video.title,
            "description": video.description,
            "category": video.category,
            "is_shared": video.is_shared,
            "status": video.status,
            "s3_key": video.s3_key,
            "created_at": video.created_at,
            "owner_id": video.owner_id,
            "file_size": video.file_size,
            "is_deleted": video.is_deleted,
            "owner_email": video.owner.email if video.owner else "Unknown User"
        })
    return results

@router.post("/{video_id}/summarize")
async def generate_video_summary(
    video_id: str,
    force: bool = False,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(main_utils.get_current_user)
):
    video = db.query(models.VideoJob).filter(models.VideoJob.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    # Ownership check — only the owner or an admin can summarize
    if video.owner_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to summarize this video")

    if not video.s3_key or video.status != "completed":
        raise HTTPException(status_code=400, detail="Video is not ready for analysis yet")

    if force:
        # Wipe existing summary from DB and cache so background task generates fresh
        db.query(models.VideoSummary).filter(models.VideoSummary.video_id == video_id).delete()
        db.commit()
        cache.delete_cached_summary(video_id)
    else:
        # Check caches — return immediately if found (no need to generate)
        cached = cache.get_cached_summary(video_id)
        if cached:
            return {"summary": cached, "status": "ready"}
        db_summary = db.query(models.VideoSummary).filter(
            models.VideoSummary.video_id == video_id
        ).first()
        if db_summary:
            cache.set_cached_summary(video_id, db_summary.summary_text)
            return {"summary": db_summary.summary_text, "status": "ready"}

    # Run AI pipeline as a background task so this endpoint returns immediately.
    # The result is pushed to the user via WebSocket (type: "summary_ready").
    background_tasks.add_task(ai_utils.generate_summary_background, video_id, current_user.id)
    return {"summary": None, "status": "generating"}
