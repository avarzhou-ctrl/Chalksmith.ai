from fastapi import APIRouter, File, UploadFile
from backend.services.sources import extract_source_context

router = APIRouter()

@router.post("/upload")
async def preview_source_upload(file: UploadFile = File(...)):
    source_context = await extract_source_context(file)
    return {
        "status": "success",
        "file_name": file.filename,
        "content_type": file.content_type,
        "preview": source_context[:1000] if source_context else "",
    }
