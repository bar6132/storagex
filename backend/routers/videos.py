from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Form
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
import models, schemas, database, tasks, main_utils
import search

router = APIRouter(prefix="/videos", tags=["Videos"])

@router.get("/feed", response_model=List[schemas.VideoOut])
def get_video_feed(
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(database.get_db)
):
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
    current_usage = db.query(func.sum(models.VideoJob.file_size)).filter(
        models.VideoJob.owner_id == current_user.id,
        models.VideoJob.is_deleted == False
    ).scalar() or 0

    if not current_user.is_admin: 
        if current_usage + file.size > current_user.storage_limit:
            raise HTTPException(status_code=400, detail="Quota exceeded!")

    new_job = models.VideoJob(
        filename=file.filename,
        title=title,
        description=description,   
        category=category,         
        is_shared=is_shared,       
        owner_id=current_user.id,
        status="pending",
        file_size=file.size 
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

@router.get("/admin/all", response_model=List[schemas.VideoOut])
async def get_all_videos_admin(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(main_utils.get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Admin access required"
        )
    return db.query(models.VideoJob).all()

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
    query = db.query(models.VideoJob).filter(
        models.VideoJob.is_shared == True,
        models.VideoJob.is_deleted == False
    )
    if category and category != "All":
        query = query.filter(models.VideoJob.category == category)
    if q:
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