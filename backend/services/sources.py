import os
from typing import Optional
from fastapi import UploadFile
from langchain_community.document_loaders import PyMuPDFLoader
import shutil

async def extract_source_context(file: Optional[UploadFile]) -> Optional[str]:
    if file is None or not file.filename:
        return None

    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # Extract text
        loader = PyMuPDFLoader(temp_path)
        documents = loader.load()
        
        full_text = "\n\n".join([doc.page_content for doc in documents])
        
        return {"status": "success", "extracted_text": full_text}
        
    finally:
        # Clean up the temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)