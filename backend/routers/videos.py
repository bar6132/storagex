from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Form
from sqlalchemy.orm import Session
from typing import List
import models, schemas, database, tasks, main_utils

router = APIRouter(prefix="/videos", tags=["Videos"])

@router.post("/upload")
async def create_upload_job(
    file: UploadFile = File(...), 
    title: str = Form(...),  
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(main_utils.get_current_user) 
):
    new_job = models.VideoJob(
        filename=file.filename,
        title=title,
        owner_id=current_user.id,
        status="pending"
    )
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    
    s3_filename = f"raw/user_{current_user.id}/{new_job.id}-{file.filename}"
    
    await file.seek(0)
    tasks.upload_to_s3(file.file, "raw-videos", s3_filename)
    tasks.notify_worker(new_job.id, s3_filename)
    
    return {"job_id": new_job.id, "status": "queued", "owner": current_user.email}

@router.get("/my-videos", response_model=List[schemas.VideoOut])
async def list_videos(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(main_utils.get_current_user)
):
    return db.query(models.VideoJob).filter(models.VideoJob.owner_id == current_user.id).all()

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
    if not video: raise HTTPException(status_code=404, detail="Video not found")
    
    is_admin = getattr(current_user, "is_admin", False) 
    if not is_admin and video.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    db.delete(video)
    db.commit()
    return {"message": "Deleted"}


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